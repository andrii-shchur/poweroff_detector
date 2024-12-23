import os
from enum import Enum

COLUMN_WIDTH: int = 58
ROW_HEIGHT: int = 43
GROUPS: tuple[str, ...] = ('1.1', '1.2', '2.1', '2.2', '3.1', '3.2')
GROUP_COUNT: int = len(GROUPS)
HOUR_COUNT: int = 24
# Offset is basically a reference point from which all the other coordinates are calculated
SCHEDULE_DATE_BOXES_TO_OFFSET: dict[tuple[int, int, int, int], tuple[int, int]] = {
    (35, 96, 184, 130): (146, 257),  # (x_top, y_top, x_bottom, y_bottom): (x_offset, y_offset)
    (297, 48, 435, 75): (146, 235),
    (39, 45, 184, 79): (147, 233),
}
NO_OUTAGES_DATE_BOX: tuple[int, int, int, int] = 688, 206, 1079, 311

# Case when there are two tables on a picture
TABLES_DIFF: int = 335

# Telegram chat id of LvivOblEnergo channel
LOE_CHAT_ID = -1001370047993

# Stuff from env variables
if not os.environ.get('PRODUCTION'):
    from dotenv import load_dotenv

    load_dotenv()
TELEGRAM_API_ID = int(os.environ.get('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT'))
POSTGRES_DB_NAME = os.environ.get('POSTGRES_DB_NAME')
POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
POSTGRES_RETRY_COUNT = int(os.environ.get('POSTGRES_RETRY_COUNT'))

STDOUT_LOGS = os.environ.get('STDOUT_LOGS')


class DayName(Enum):
    TODAY = 'сьогодні'
    TOMORROW = 'завтра'
