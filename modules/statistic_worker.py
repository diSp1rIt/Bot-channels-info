from data import db_session
from data.channels import *
from telethon.tl import patched
from tqdm import tqdm

db_session.global_init('msgs_database.db')
db_ses = db_session.create_session()

data_list = [
    'full_chat.id',
    'chats[0].title',
    'full_chat.pts',
    'full_chat.participants_count',
    'full_chat.pinned_msg_id'
]

labels_list = [
    'ID',
    'Название',
    'Кол-во постов',
    'Кол-во подписчиков',
    'ID закрепленного сообщения'
]


def get_current_info(channel):
    text = []

    for i in range(len(data_list)):
        text.append(labels_list[i] + ': ' + str(eval(f'channel.{data_list[i]}')))

    text = '\n\n'.join(text)
    return text


async def do_record(channel):
    new_channel = Channel()
    for i in range(len(data_list)):
        if 'full_chat' in data_list[i]:
            exec(f'new_channel{data_list[i].split("full_chat")[1]} = channel.{data_list[i]}')
        else:
            if data_list[i].split("chats[0]")[1] == '.photo':
                exec(f'new_channel{data_list[i].split("chats[0]")[1]} = str(channel.{data_list[i]})')
            else:
                exec(f'new_channel{data_list[i].split("chats[0]")[1]} = channel.{data_list[i]}')
    db_ses.add(new_channel)
    db_ses.commit()


async def delete_data(channel_id: int, delete_from_channels=False, delete_from_posts=False):
    if delete_from_channels:
        result = db_ses.query(Channel).filter(Channel.id == channel_id)
        for channel in result:
            db_ses.delete(channel)
        db_ses.commit()
    if delete_from_posts:
        result = db_ses.query(Post).filter(Post.channel_id == channel_id)
        for channel in result:
            db_ses.delete(channel)
        db_ses.commit()


async def load_channels(client):
    analyze_list = []
    db_res = list(set(db_ses.query(Channel).all()))
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            dialog = dialog.entity
            if dialog.id in [elem.id for elem in db_res]:
                analyze_list.append(dialog)
    return analyze_list


async def messages_dump(client, analyze_list, including_range: dict):
    for channel in tqdm(analyze_list):
        async for msg in client.iter_messages(channel.id):
            if type(msg) is patched.Message:
                msg: patched.Message
                if msg.message != '':
                    if msg.date.year in including_range.keys():
                        if msg.date.month in including_range[msg.date.year]:
                            new_post = Post()
                            new_post.message_id = msg.id
                            new_post.channel_id = msg.to_id.channel_id
                            new_post.message = msg.message.lower()
                            new_post.views = msg.views
                            new_post.post_date = msg.date
                            db_ses.add(new_post)
    db_ses.commit()


async def find_messages_by_word(word: str, channel_id=None):
    word = word.lower()
    if channel_id is None:
        result = db_ses.query(Post).filter(Post.message.like(f'%{word}%')).all()
    else:
        if type(channel_id) is int or str(channel_id).isdigit():
            channel_id = int(channel_id)
            result = db_ses.query(Post).filter(Post.message.like(f'%{word}%')).filter(
                Post.channel_id == channel_id).all()
        else:
            return 'Didn\'t find'
    answer = dict()
    for post in result:
        answer[post.channel_id] = [post.message_id, post.message.count(word)]
    return answer
