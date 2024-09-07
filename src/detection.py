import io
from collections import defaultdict
from datetime import date, datetime

import pytesseract
from PIL import Image
from pydantic import BaseModel, Field, model_validator

from const import (
    COLUMN_WIDTH,
    DATE_BOX,
    GROUP_COUNT,
    GROUPS,
    HOUR_COUNT,
    ROW_HEIGHT,
    TABLES_DIFF,
    X_OFFSET,
    Y_OFFSET,
)


class OnOffInterval(BaseModel):
    state: str = Field(pattern=r'^(on|off)$')
    start_hour: int = Field(ge=0, le=24)
    end_hour: int = Field(ge=0, le=24)

    @model_validator(mode='after')
    def check_end_greater_than_start_hour(self):
        assert self.end_hour > self.start_hour
        return self

    def __str__(self):
        return f'{self.start_hour}:00 - {self.end_hour}:00'


def get_coordinates_map() -> list[tuple[int, int]]:
    result = []
    tables_split_at = 12
    for hour in range(HOUR_COUNT):
        for group in range(GROUP_COUNT):
            additional_offset = TABLES_DIFF if hour >= tables_split_at else 0
            result.append(
                (
                    X_OFFSET + COLUMN_WIDTH * (hour % tables_split_at),
                    Y_OFFSET + ROW_HEIGHT * group + additional_offset,
                )
            )
    return result


def detect_on_off(image_blob: bytes) -> dict[str, list[bool]]:
    image = Image.open(io.BytesIO(image_blob))
    pixels = image.load()
    status = defaultdict(list)
    coordinates_map = get_coordinates_map()
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


def detect_date(image_blob: bytes) -> date | None:
    image = Image.open(io.BytesIO(image_blob))
    date_str = pytesseract.image_to_string(image.crop(DATE_BOX)).strip()
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return None  # date not detected -> skip image as it's not a schedule