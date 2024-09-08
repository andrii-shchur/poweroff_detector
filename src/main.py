import asyncio
import logging

from telethon.sync import TelegramClient, events

from bot import send_updates
from const import LOE_CHAT_ID, TELEGRAM_API_HASH, TELEGRAM_API_ID
from detection import get_date_and_schedule

log = logging.getLogger(__name__)


def process_schedule_update(image_blob: bytes | None) -> None:
    if image_blob is None:
        log.info('Skipping messsage, no image')
        return
    schedule_date, schedule = get_date_and_schedule(image_blob)
    log.info(f'Detected date: {schedule_date}. Detected schedule: {schedule}')
    asyncio.ensure_future(send_updates(schedule_date, schedule))


if __name__ == '__main__':
    with TelegramClient('/app/poweroff_detector.session', TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:

        @client.on(events.NewMessage(chats=LOE_CHAT_ID))
        async def handler(event: events.NewMessage.Event) -> None:
            blob = await event.message.download_media(bytes)
            process_schedule_update(blob)

        client.run_until_disconnected()
