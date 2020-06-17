from telethon import TelegramClient, sync
from cfg_loader import *
from decorators import async_call

client_data = load_configs()
API_ID = client_data['API_ID']
API_HASH = client_data['API_HASH']
client = TelegramClient('bot', API_ID, API_HASH)


@async_call
async def send_code(phone: str) -> None:
    await client.send_code_request(phone)


@async_call
async def sing_in(phone: str, code: int) -> None:
    await client.sign_in(phone, code)


def get_client() -> TelegramClient:
    return client
