import json
from pre_cfg import API_ID, API_HASH
from os.path import exists

if not exists('config.json'):
    with open('config.json', 'w') as f:
        data = {
            'API_ID': API_ID,
            'API_HASH': API_HASH,
            'OWNER_ID': None
        }
        json.dump(data, f)


def get_data() -> tuple:
    data = dict()
    with open('config.json', 'r') as f:
        nonlocal data
        data = json.load(f)
    return data["API_ID"], data["API_HASH"], data["OWNER_ID"]


def set_data(key: str, value):
    data = dict()
    with open('config.json', 'r') as f:
        nonlocal data
        data = json.load(f)
