import asyncio
import logging

from telethon.sync import TelegramClient, events

from bot import send_updates
from const import LOE_CHAT_ID, TELEGRAM_API_HASH, TELEGRAM_API_ID
from detection import detect_date, detect_on_off, prettify_detection

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


def process_schedule_update(image_blob: bytes | None) -> None:
    if image_blob is None:
        log.info('Skipping messsage, no image')
        return
    if (schedule_date := detect_date(image_blob)) is None:
        log.info('Skipping image, no schedule')
        return
    log.info(f'Detected date: {schedule_date}')
    schedule = detect_on_off(image_blob)
    schedule = prettify_detection(schedule)
    asyncio.ensure_future(send_updates(schedule, schedule_date))


if __name__ == '__main__':
    with TelegramClient('/app/poweroff_detector.session', TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:

        @client.on(events.NewMessage(chats=LOE_CHAT_ID))
        async def handler(event: events.NewMessage.Event) -> None:
            blob = await event.message.download_media(bytes)
            process_schedule_update(blob)

        client.run_until_disconnected()
