import psycopg2

from const import (
    POSTGRES_DB_NAME,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_RETRY_COUNT,
    POSTGRES_USER,
)

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
        continue
    else:
        break


def create_subscriptions_table_if_not_exists():
    with conn.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS public.subscriptions "
            "( id SERIAL PRIMARY KEY, group_name VARCHAR(3) NOT NULL, chat_id BIGINT NOT NULL);"
        )
        conn.commit()


def set_group_subscription(group_name: str, chat_id: int):
    with conn.cursor() as cursor:
        cursor.execute(f"INSERT INTO public.subscriptions (group_name, chat_id) VALUES ({group_name}, {chat_id})")
        conn.commit()


def delete_group_subscription(group_name: str, chat_id: int):
    with conn.cursor() as cursor:
        cursor.execute(f"DELETE FROM public.subscriptions WHERE group_name='{group_name}' AND chat_id={chat_id}")
        conn.commit()


def get_chat_ids_for_group() -> dict[str, list[int]]:
    with conn.cursor() as cursor:
        cursor.execute("SELECT group_name, array_agg(chat_id) FROM public.subscriptions GROUP BY group_name")
        return dict(cursor.fetchall())


def get_groups_by_chat_id(chat_id: int) -> set[str]:
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT group_name FROM public.subscriptions WHERE chat_id={chat_id}")
        return set(el[0] for el in cursor.fetchall())
