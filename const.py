# Basically a reference point from which all the other coordinates are calculated
X_OFFSET: int = 146
Y_OFFSET: int = 244

COLUMN_WIDTH: int = 58
ROW_HEIGHT: int = 43
GROUPS: tuple[str, ...] = ('1.1', '1.2', '2.1', '2.2', '3.1', '3.2')
GROUP_COUNT: int = len(GROUPS)
HOUR_COUNT: int = 24
DATE_BOX: tuple[int, int, int, int] = 282, 42, 439, 79  # x_top, y_top, x_bottom, y_bottom

# Case when there are two tables on a picture
TABLES_DIFF: int = 335
