from telethon import TelegramClient, sync
from cfg_loader import *

client_data = load_configs()
API_ID = client_data['API_ID']
API_HASH = client_data['API_HASH']
client = TelegramClient('bot', API_ID, API_HASH)
client.connect()
loop = None


async def send_code(phone: str) -> None:
    global client

    await client.send_code_request(phone)


async def sing_in(phone: str, code: int) -> None:
    global client

    await client.sign_in(phone, code)


def get_client() -> TelegramClient:
    global client

    return client


def set_loop(custom_loop) -> None:
    global loop
    loop = custom_loop
