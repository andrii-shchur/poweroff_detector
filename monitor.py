import os

from telethon.sync import TelegramClient, events

from detection import test_coordinates_map

if not os.environ.get('PRODUCTION'):
    from dotenv import load_dotenv

    load_dotenv()

TELEGRAM_API_ID = int(os.environ.get('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
LOE_CHAT_ID = -1001370047993

with TelegramClient('poweroff_detector', TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:

    @client.on(events.NewMessage(chats=LOE_CHAT_ID))
    async def handler(event: events.NewMessage.Event) -> None:
        blob = await event.message.download_media(bytes)
        test_coordinates_map(blob)

    client.run_until_disconnected()
