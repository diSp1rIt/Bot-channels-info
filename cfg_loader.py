import json
from pre_cfg import *
from os.path import exists

if not exists('config.json'):
    with open('config.json', 'w') as f:
        data = {
            'API_ID': API_ID,
            'API_HASH': API_HASH,
            'OWNER_ID': None,
            'TOKEN': TOKEN,
            'SECRET_KEY': SECRET_KEY
        }
        json.dump(data, f)


def load_configs() -> dict:
    with open('config.json', 'r') as f:
        data = json.load(f)
    return data


def set_config(key: str, value) -> None:
    with open('config.json', 'r') as f:
        data = json.load(f)

    if key not in data.keys() or key == 'SECRET_KEY':
        raise KeyError('Недопустимый ключ')
    else:
        data[key] = value

    with open('config.json', 'w') as f:
        json.dump(data, f)
