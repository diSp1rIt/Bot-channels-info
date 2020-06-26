import argparse

parser = argparse.ArgumentParser(description='Installation script for "Bot channel\'s info"')
parser.add_argument('token', type=str, metavar='BOT_TOKEN', help='Bot api token')
parser.add_argument('api_id', type=int, metavar='API_ID', help='Telegram API id')
parser.add_argument('api_hash', type=str, metavar='API_HASH', help='Telegram API hash')
parser.add_argument('secret_key', type=str, metavar='SECRET_KEY', help='Secret key for auth in bot')

args = parser.parse_args()

with open('pre_cfg.py', 'w') as f:
    lines = [
        f'TOKEN = \'{args.token}\'',
        f'API_ID = {args.api_id}',
        f'API_HASH = \'{args.api_hash}\'',
        f'SECRET_KEY = \'{args.secret_key}\''
    ]
    f.writelines(*lines)

print('Installed')
