import telethon
import asyncio

loop = asyncio.new_event_loop()
client = telethon.TelegramClient('bot', )

async def send_code(phone):
    pass