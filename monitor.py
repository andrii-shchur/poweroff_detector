from telethon.sync import TelegramClient, events

from const import LOE_CHAT_ID, TELEGRAM_API_HASH, TELEGRAM_API_ID
from detection import test_coordinates_map

with TelegramClient('poweroff_detector', TELEGRAM_API_ID, TELEGRAM_API_HASH) as client:

    @client.on(events.NewMessage(chats=LOE_CHAT_ID))
    async def handler(event: events.NewMessage.Event) -> None:
        blob = await event.message.download_media(bytes)
        test_coordinates_map(blob)

    client.run_until_disconnected()
