import datetime
import logging
import time

import psycopg2

from const import (
    POSTGRES_DB_NAME,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_RETRY_COUNT,
    POSTGRES_USER,
)

log = logging.getLogger(__name__)

for _ in range(POSTGRES_RETRY_COUNT):
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB_NAME,
            port=POSTGRES_PORT,
        )
    except psycopg2.OperationalError:
        time.sleep(2)
        continue
    else:
        break
else:
    log.critical(f'Could not connect to database: {POSTGRES_DB_NAME}')


# TODO: make more generic
def list_to_postgres_array(lst: list) -> str:
    if all(isinstance(el, bool) for el in lst):
        return f'{{{",".join(map(str, lst))}}}'.lower()
    else:
        raise NotImplementedError(
            f'Converting list to postgres array for types {set(map(type, lst)) - {bool}} is not implemented yet'
        )


def create_tables_if_not_exists() -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS public.subscriptions "
            "( id SERIAL PRIMARY KEY, group_name VARCHAR(3) NOT NULL, chat_id BIGINT NOT NULL);"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS public.recent_schedules "
            "( id SERIAL PRIMARY KEY, s_date DATE NOT NULL, group_name VARCHAR(3) NOT NULL, "
            "schedule bool[24] NOT NULL);"
        )
        conn.commit()


def set_group_subscription(group_name: str, chat_id: int) -> None:
    with conn.cursor() as cursor:
        cursor.execute(f"INSERT INTO public.subscriptions (group_name, chat_id) VALUES ({group_name}, {chat_id})")
        conn.commit()


def delete_group_subscription(group_name: str, chat_id: int) -> None:
    with conn.cursor() as cursor:
        cursor.execute(f"DELETE FROM public.subscriptions WHERE group_name='{group_name}' AND chat_id={chat_id}")
        conn.commit()


def get_chat_ids_for_groups() -> dict[str, list[int]]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT group_name, array_agg(chat_id) FROM public.subscriptions GROUP BY group_name")
        return dict(cursor.fetchall())


def get_groups_by_chat_id(chat_id: int) -> set[str]:
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT group_name FROM public.subscriptions WHERE chat_id={chat_id}")
        return set(el[0] for el in cursor.fetchall())


# this query consists of 2 queries. first one updates schedule if it exists, otherwise it will have no effect
# second one inserts schedule if it doesn't exist, otherwise the query has no effect because it will insert nothing
# (SELECT 1 FROM public.recent_schedules WHERE ... will return nothing)
def upsert_recent_schedule(date: datetime.date, group_name: str, schedule: list[bool]) -> None:
    date_str = date.strftime("%Y-%m-%d")
    schedule_str = list_to_postgres_array(schedule)
    with conn.cursor() as cursor:
        cursor.execute(
            f"UPDATE public.recent_schedules "
            f"SET s_date='{date_str}', group_name='{group_name}', schedule='{schedule_str}' "
            f"WHERE s_date='{date_str}' AND group_name='{group_name}'; "
            f"INSERT INTO public.recent_schedules (s_date, group_name, schedule) "
            f"SELECT '{date_str}', '{group_name}', '{schedule_str}' WHERE NOT EXISTS "
            f"(SELECT 1 FROM public.recent_schedules WHERE s_date='{date_str}' AND group_name='{group_name}');"
        )
        conn.commit()


def get_recent_schedules_for_groups(date: datetime.date) -> dict[str, list[bool]]:
    date_str = date.strftime("%Y-%m-%d")
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT group_name, schedule FROM public.recent_schedules WHERE s_date='{date_str}'")
        return dict(cursor.fetchall())
