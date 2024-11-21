import io
import logging
from collections import defaultdict
from datetime import date, datetime

import dateparser
import pytesseract
from PIL import Image
from pydantic import BaseModel, Field, model_validator

from const import (
    COLUMN_WIDTH,
    GROUP_COUNT,
    GROUPS,
    HOUR_COUNT,
    NO_OUTAGES_DATE_BOX,
    ROW_HEIGHT,
    SCHEDULE_DATE_BOXES_TO_OFFSET,
    TABLES_DIFF,
)

log = logging.getLogger(__name__)


class OnOffInterval(BaseModel):
    state: str = Field(pattern=r'^(on|off)$')
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=0, le=24)

    @model_validator(mode='after')
    def check_end_greater_than_start_hour(self):
        assert self.end_hour > self.start_hour
        return self

    def __str__(self):
        return f'{self.start_hour}:00 - {self.end_hour}:00'


def get_coordinates_map(x_offset: int, y_offset: int) -> list[tuple[int, int]]:
    result = []
    tables_split_at = 12
    for hour in range(HOUR_COUNT):
        for group in range(GROUP_COUNT):
            additional_offset = TABLES_DIFF if hour >= tables_split_at else 0
            result.append(
                (
                    x_offset + COLUMN_WIDTH * (hour % tables_split_at),
                    y_offset + ROW_HEIGHT * group + additional_offset,
                )
            )
    return result


def detect_on_off(image_blob: bytes, x_offset: int, y_offset: int) -> dict[str, list[bool]]:
    image = Image.open(io.BytesIO(image_blob))
    pixels = image.load()
    status = defaultdict(list)
    coordinates_map = get_coordinates_map(x_offset, y_offset)
    for i in range(GROUP_COUNT):
        for j in range(HOUR_COUNT):
            status[GROUPS[i]].append(pixels[*coordinates_map[i + GROUP_COUNT * j]][0] < 200)
    return status


def prettify_detection(detection: dict[str, list[bool]]) -> dict[str, list[OnOffInterval]]:
    pretty_schedule = defaultdict(list)
    for group, on_offs in detection.items():
        # set initial reference states
        reference_hour = 0
        reference_state = on_offs[0]
        # iterate through 1-24 hours
        for hour, state in enumerate(on_offs[1:], start=1):
            # if on/off state at certain hour has changed, we save it as a OnOffInterval object
            if state != reference_state:
                on_off_interval = OnOffInterval(
                    state='on' if reference_state else 'off', start_hour=reference_hour, end_hour=hour
                )
                pretty_schedule[group].append(on_off_interval)
                # reset reference states and go again
                reference_hour = hour
                reference_state = state
        on_off_interval = OnOffInterval(state='on' if state else 'off', start_hour=reference_hour, end_hour=24)
        pretty_schedule[group].append(on_off_interval)

    return pretty_schedule


def detect_date_on_schedule(image_blob: bytes) -> tuple[date, int, int] | None:
    image = Image.open(io.BytesIO(image_blob))
    for box, x_y_offset in SCHEDULE_DATE_BOXES_TO_OFFSET.items():
        date_str = pytesseract.image_to_string(image.crop(box)).strip()
        try:
            return datetime.strptime(date_str, '%d.%m.%Y').date(), *x_y_offset
        except ValueError:
            pass
    return None  # date not detected -> skip image as it's not a schedule


def detect_no_outages_date(image_blob: bytes) -> date | None:
    image = Image.open(io.BytesIO(image_blob))
    image_text = pytesseract.image_to_string(image, lang='ukr').replace('\n', ' ')
    if 'графіки погодинних відключень не застосовуватимуть' in image_text:
        date_str = pytesseract.image_to_string(image.crop(NO_OUTAGES_DATE_BOX).convert('L'), lang='ukr').strip()
        parsed_date = dateparser.parse(date_str, languages=('uk',))
        return parsed_date.date() if parsed_date else None


def get_date_and_schedule(image_blob: bytes) -> tuple[date, dict[str, list[bool]]] | None:
    if (result := detect_date_on_schedule(image_blob)) is not None:
        schedule_date, x_offset, y_offset = result
        schedule = detect_on_off(image_blob, x_offset, y_offset)
        return schedule_date, schedule
    else:
        log.info('No schedule found')
        if (no_outages_date := detect_no_outages_date(image_blob)) is not None:
            log.info('Found "no outages" image')
            no_outages_schedule = dict((group, [True for _ in range(HOUR_COUNT)]) for group in GROUPS)
            return no_outages_date, no_outages_schedule
        else:
            log.info('Skipping image, neither any schedule nor "no outages" found')
            return
