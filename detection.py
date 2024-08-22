from collections import defaultdict
from datetime import date, datetime

import pytesseract
from PIL import Image

from const import HOUR_COUNT, GROUP_COUNT, TABLES_DIFF, X_OFFSET, COLUMN_WIDTH, Y_OFFSET, ROW_HEIGHT, GROUPS, DATE_BOX


def get_coordinates_map() -> list[tuple[int, int]]:
    result = []
    tables_split_at = 12
    for hour in range(HOUR_COUNT):
        for group in range(GROUP_COUNT):
            additional_offset = TABLES_DIFF if hour > tables_split_at else 0
            result.append(
                (
                    X_OFFSET + COLUMN_WIDTH * (hour % tables_split_at),
                    Y_OFFSET + ROW_HEIGHT * group + additional_offset,
                )
            )
    return result


def detect_on_off(filename: str) -> dict[str, list[bool]]:
    image = Image.open(filename)
    pixels = image.load()
    status = defaultdict(list)
    coordinates_map = get_coordinates_map()
    for i in range(GROUP_COUNT):
        for j in range(HOUR_COUNT):
            status[GROUPS[i]].append(
                pixels[*coordinates_map[i + GROUP_COUNT * j]][0] < 200
            )
    return status


def detect_date(filename: str) -> date:
    image = Image.open(filename)
    date_str = pytesseract.image_to_string(image.crop(DATE_BOX)).strip()
    return datetime.strptime(date_str, '%d.%m.%Y').date()


# FOR DEBUG PURPOSES
if __name__ == '__main__':
    image = Image.open('img.png')
    coordinates_map = get_coordinates_map()
    pixels = image.load()
    # for x, y in coordinates_map:
    #     pixels[x, y] = (255, 0, 0)
    # image.show()

    for i in range(GROUP_COUNT):
        for j in range(HOUR_COUNT):
            # print(coordinates_map[i + image_params.group_count * j], end=' ')
            print('🟩' if pixels[*coordinates_map[i + GROUP_COUNT * j]][0] < 200 else '🟥', end='')
        print()

    print(detect_date('img.png'))
