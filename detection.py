from PIL import Image

X_OFFSET = 104
Y_OFFSET = 286
COLUMN_WIDTH = 58
ROW_HEIGHT = 43
GROUP_COUNT = 6
HOUR_COUNT = 24
coordinates_map = [
    (X_OFFSET + COLUMN_WIDTH * hour, Y_OFFSET + ROW_HEIGHT * group)
    for hour in range(HOUR_COUNT)
    for group in range(GROUP_COUNT)
]

image = Image.open('img.png')

pixels = image.load()
status = {}
for i in range(GROUP_COUNT):
    for j in range(HOUR_COUNT):
        print('🟩' if pixels[*coordinates_map[i+GROUP_COUNT*j]][0] < 200 else '🟥', end='')
    print()


# image.show()
