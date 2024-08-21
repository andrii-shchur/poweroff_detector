from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime

import pytesseract
from PIL import Image


@dataclass
class ImageParams:
    x_offset: int = 147
    y_offset: int = 260
    column_width: int = 58
    row_height: int = 43
    tables_diff: int = 335  # case when there are two tables on a picture
    groups: tuple[str, ...] = ('1.1', '1.2', '2.1', '2.2', '3.1', '3.2')
    hour_count: int = 24
    date_box: tuple[int, int, int, int] = 664, 0, 879, 71  # x_top, y_top, x_bottom, y_bottom

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def coordinates_map(self) -> list[tuple[int, int]]:
        result = []
        tables_split_at = 12
        for hour in range(self.hour_count):
            for group in range(self.group_count):
                additional_offset = self.tables_diff if hour > tables_split_at else 0
                result.append(
                    (
                        self.x_offset + self.column_width * (hour % tables_split_at),
                        self.y_offset + self.row_height * group + additional_offset,
                    )
                )
        return result


def detect_on_off(filename: str, image_params: ImageParams) -> dict[str, list[bool]]:
    image = Image.open(filename)
    pixels = image.load()
    status = defaultdict(list)
    for i in range(image_params.group_count):
        for j in range(image_params.hour_count):
            status[image_params.groups[i]].append(
                pixels[*image_params.coordinates_map[i + image_params.group_count * j]][0] < 200
            )
    return status


def detect_date(filename: str, image_params: ImageParams) -> date:
    image = Image.open(filename)
    date_str = pytesseract.image_to_string(image.crop(image_params.date_box)).strip()
    return datetime.strptime(date_str, '%d.%m.%Y').date()


# FOR DEBUG PURPOSES
if __name__ == '__main__':
    image = Image.open('img.png')
    image_params = ImageParams()
    coordinates_map = image_params.coordinates_map
    pixels = image.load()
    # for x, y in coordinates_map:
    #     pixels[x, y] = (255, 0, 0)
    # image.show()

    for i in range(image_params.group_count):
        for j in range(image_params.hour_count):
            # print(coordinates_map[i + image_params.group_count * j], end=' ')
            print('🟩' if pixels[*coordinates_map[i + image_params.group_count * j]][0] < 200 else '🟥', end='')
        print()
