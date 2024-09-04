import io
from collections import defaultdict
from datetime import date, datetime

import pytesseract
from PIL import Image

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


def detect_on_off(image: bytes) -> dict[str, list[bool]]:
    image = Image.open(io.BytesIO(image))
    pixels = image.load()
    status = defaultdict(list)
    coordinates_map = get_coordinates_map()
    for i in range(GROUP_COUNT):
        for j in range(HOUR_COUNT):
            status[GROUPS[i]].append(pixels[*coordinates_map[i + GROUP_COUNT * j]][0] < 200)
    return status


def detect_date(filename: str) -> date | None:
    image = Image.open(filename)
    date_str = pytesseract.image_to_string(image.crop(DATE_BOX)).strip()
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return None  # date not detected -> skip image as it's not a schedule


# FOR DEBUG PURPOSES
def test_coordinates_map(image: bytes | None = None) -> None:
    image = Image.open(io.BytesIO(image)) if image else Image.open('img.png')
    coordinates_map = get_coordinates_map()
    pixels = image.load()
    # for x, y in coordinates_map:
    #     pixels[x, y] = (255, 0, 0)
    # image.show()

    for i in range(GROUP_COUNT):
        for j in range(HOUR_COUNT):
            # print(coordinates_map[i + GROUP_COUNT * j], end=' ')
            print('🟩' if pixels[*coordinates_map[i + GROUP_COUNT * j]][0] < 200 else '🟥', end='')
        print()


if __name__ == '__main__':
    test_coordinates_map()
    print(detect_date('img.png'))
