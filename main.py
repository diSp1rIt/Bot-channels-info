from aiogram import Bot, types, Dispatcher, executor
from cfg_loader import *
from modules import registration
from modules.handle_phone_number import check_phone_number
from telethon.tl.functions.channels import GetFullChannelRequest
from modules.statistic_worker import *
from asyncio import sleep
from datetime import datetime
from os.path import getsize
from shutil import copyfile

# ------ Init ------
configs = load_configs()
# ------------------


# ------ Global variables ------
bot = Bot(token=configs['TOKEN'])
dp = Dispatcher(bot)
client = registration.get_client()
channels_list = []
analyzing_channels_list = []
channel_id_for_delete = 0
current_month = datetime.now().month
current_year = datetime.now().year
delta_month = 0
# ------------------------------


# ------ Global functions ------
async def msg_error_handler(msg: types.Message, flag_name: str, list_type=None) -> int:
    global analyzing_channels_list

    if list_type is None:
        list_type = analyzing_channels_list

    if msg.text == '/cancel':
        await msg.answer('Отмена', reply_markup=types.ReplyKeyboardRemove())
        exec(flag_name + ' = False')
        return 1

    try:
        id = int(msg.text.split('(')[1].strip(')'))
    except Exception:
        await msg.answer('Ошибка формата.\nИспользуйте кнопки')
        return 1

    if id not in [el.id for el in list_type]:
        await msg.answer('Канал не найден')
        return 1

    return 0


async def get_channel_info_from_msg(msg: types.Message):
    global analyzing_channels_list

    index = [el.id for el in analyzing_channels_list].index(int(msg.text.split('(')[1].strip(')')))
    channel = analyzing_channels_list[index]
    result = await client(GetFullChannelRequest(channel.id))

    return result


async def update_data():
    global analyzing_channels_list
    global client

    analyzing_channels_list = await load_channels(client)
    if analyzing_channels_list:
        await bot.send_message(configs['OWNER_ID'], Done + 'Обновление\nПожалуйста подождите⏰')

        including_range = dict()
        month = current_month - delta_month
        year = current_year

        while month < 0:
            year -= 1
            month += 12
            if month < 0:
                including_range[year] = list(range(1, 13))
            else:
                including_range[year] = list(range(month, 13))
                month = 1

        including_range[current_year] = list(range(month, current_month + 1))

        await messages_dump(client, analyzing_channels_list, including_range)
        for channel in analyzing_channels_list:
            await delete_data(channel.id, delete_from_channels=True)
            res = await client(GetFullChannelRequest(channel.id))
            await do_record(res)
        await bot.send_message(configs['OWNER_ID'], 'Обновление закончено')
    return


async def wipe_db():
    global db_ses
    global db_session
    global analyzing_channels_list

    await bot.send_message(configs['OWNER_ID'], _Warning + 'Создание дампа\nПожалуйста подождите⏰')
    await bot.send_document(configs['OWNER_ID'], types.InputFile('msgs_database.db', f'msg_dump_{current_month}.{current_year}.db'))

    for channel in analyzing_channels_list:
        await delete_data(channel.id, delete_from_posts=True)

    await bot.send_message(configs['OWNER_ID'], 'Очистка закончена')


async def scheduled_actions():
    global current_month
    global current_year

    while True:

        if datetime.now().month == (current_month % 12) + 1:
            await wipe_db()
            if current_month == 12:
                current_year += 1
            current_month %= 12
            current_month += 1

        try:
            await update_data()
        except:
            pass

        await sleep(12 * 60 * 60)  # delay 12 hours
# ------------------------------


# ------ Upload data about channels ------
if client.is_user_authorized():
    # dp.loop.create_task(scheduled_actions())
    pass
else:
    if configs['OWNER_ID'] is not None:
        dp.loop.create_task(bot.send_message(configs['OWNER_ID'], 'Требуется заного пройти регистрацию'))
        dp.loop.create_task(bot.send_message(configs['OWNER_ID'], 'Введите: /login'))
# ----------------------------------------


# ------ Flags ------
phone_require = False
code_require = False
channel_name_require = False
channel_name_for_analyze_require = False
channel_name_for_delete_require = False
confirm_for_delete_require = False
# -------------------


# ------ Constants ------
Done = '🟢'
_Warning = '🟡'
Error = '🔴'
Info = '🔵'
# -----------------------


# ------ Temp variables ------
wait_for_secret_key = []
phone = ''
code = 0
# ----------------------------


@dp.message_handler(commands=['start'])
async def start_handle(msg: types.Message):
    global wait_for_secret_key
    global configs

    if configs['OWNER_ID'] is None:
        await msg.answer('Требуется ввести ключ')
        wait_for_secret_key.append(msg.chat.id)
        await msg.answer('Введите ключ от разработчика:')
    else:
        if msg.chat.id != configs['OWNER_ID']:
            await msg.answer('Доступ закрыт')
        else:
            await msg.answer('Ввод ключа от разработчика не требуется')


@dp.message_handler(commands=['login'])
async def login_handle(msg: types.Message):
    global configs
    global phone_require
    global client

    if await client.is_user_authorized():
        await msg.answer('Регистрация не требуется')
        return
    if configs['OWNER_ID'] is None:
        await msg.answer('Требуется ввести ключ')
        await msg.answer('Введите команду /start')
    else:
        if configs['OWNER_ID'] != msg.chat.id:
            await msg.answer('Доступ закрыт')
        else:
            await msg.answer('Начинаю регистрацию...')
            await msg.answer('Введите номер телефона:')
            phone_require = True


@dp.message_handler(commands=['update_list'])
async def list_channels_handle(msg: types.Message):
    global client
    global channels_list

    if configs['OWNER_ID'] != msg.chat.id:
        await msg.answer('Доступ закрыт')
        return

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        return

    text = []
    await msg.answer('Обновляю список.\nПожалуйста подождите⏰')
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            dialog = dialog.entity
            if dialog.id not in [elem.id for elem in analyzing_channels_list]:
                text.append(dialog.title + '\n' + Error + f'Не анализируется')
            else:
                text.append(dialog.title + '\n' + Done + f'Анализируется')
            if dialog.id not in [elem.id for elem in channels_list]:
                channels_list.append(dialog)
    await msg.answer('\n\n'.join(text))
    await msg.answer('Добавить к анализу:\n/add_to_analyze')


@dp.message_handler(commands=['add_to_analyze'])
async def channel_handle(msg: types.Message):
    global client
    global channels_list
    global channel_name_require

    if configs['OWNER_ID'] != msg.chat.id:
        await msg.answer('Доступ закрыт')
        return

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        return

    if len(channels_list) == 0:
        await msg.answer('Обновите список командой\n/update_list')
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    items = [types.KeyboardButton('/cancel')]
    temp_list = []
    for channel in channels_list:
        if channel.id not in [elem.id for elem in analyzing_channels_list]:
            temp_list.append(channel)
    items.extend([types.KeyboardButton(elem.title + f'\n({elem.id})') for elem in temp_list])
    markup.add(*items)
    channel_name_require = True
    await msg.answer('Выберете канал', reply_markup=markup)


@dp.message_handler(commands=['remove_from_analyze'])
async def remove_from_analyze_handle(msg: types.Message):
    global client
    global analyzing_channels_list
    global channel_name_for_delete_require

    if configs['OWNER_ID'] != msg.chat.id:
        await msg.answer('Доступ закрыт')
        return

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        return

    if not analyzing_channels_list:
        await msg.answer('Список анализируемых групп пуст')
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    items = [types.KeyboardButton('/cancel')]
    temp_list = analyzing_channels_list
    items.extend([types.KeyboardButton(elem.title + f'\n({elem.id})') for elem in temp_list])
    markup.add(*items)
    channel_name_for_delete_require = True
    await msg.answer('Выберете канал', reply_markup=markup)


@dp.message_handler(commands=['analyze_list'])
async def analyze_list_handle(msg: types.Message):
    global client
    global analyzing_channels_list

    if configs['OWNER_ID'] != msg.chat.id:
        await msg.answer('Доступ закрыт')
        return

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        return

    if not analyzing_channels_list:
        await msg.answer('Список анализируемых групп пуст')
        return

    text = []
    for channel in analyzing_channels_list:
        text.append(Info + channel.title)
    await msg.answer('\n\n'.join(text))


@dp.message_handler(commands=['get_channel_info'])
async def get_info_handle(msg: types.Message):
    global client
    global channels_list
    global channel_name_for_analyze_require

    if configs['OWNER_ID'] != msg.chat.id:
        await msg.answer('Доступ закрыт')
        return

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        return

    if len(analyzing_channels_list) == 0:
        await msg.answer('Список анализируемых каналов пустой')
        await msg.answer('Обновите список командой\n/update_list')
        return
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        items = [types.KeyboardButton('/cancel')]
        items.extend(
            [types.KeyboardButton(channel.title + f'\n({channel.id})') for channel in analyzing_channels_list])
        markup.add(*items)
        await msg.answer('Выберете канал для получения информации', reply_markup=markup)
        channel_name_for_analyze_require = True


@dp.message_handler(commands=['get_database'])
async def get_db_handle(msg: types.Message):
    global client

    if configs['OWNER_ID'] != msg.chat.id:
        await msg.answer('Доступ закрыт')
        return

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        return

    if getsize('msgs_database.db') / 1000 / 1000 >= 50:
        copyfile('msgs_database.db', f'msg_dump_{current_month}.{current_year}.db')
        await msg.answer('База имеет слишком большой объём для отправки')
    else:
        await bot.send_document(msg.chat.id, types.InputFile('msgs_database.db', f'msg_dump_{current_month}.{current_year}.db'))


@dp.message_handler(content_types=['text'])
async def text_handle(msg: types.Message):
    global wait_for_secret_key
    global configs
    global phone
    global phone_require
    global code
    global code_require
    global client
    global channel_name_require
    global channel_name_for_analyze_require
    global confirm_for_delete_require
    global channel_id_for_delete
    global channel_name_for_delete_require

    if msg.chat.id not in wait_for_secret_key:
        # Если ключ разработчика не требуется
        if configs['OWNER_ID'] is None:
            await msg.answer('Вы не начали работу')
        else:
            if msg.chat.id != configs['OWNER_ID']:
                await msg.answer('Доступ закрыт')
            else:

                if phone_require:
                    try:
                        phone = check_phone_number(msg.text)
                    except ValueError as error:
                        await msg.answer(f'Неверный формат номер телефона: {str(error)}')
                    else:
                        await msg.answer(f'Ваш номер: {phone}')
                        try:
                            dp.loop.create_task(registration.send_code(phone))
                        except Exception as error:
                            await msg.answer('Телеграм не принимает этот телефон')
                            print(error)
                        else:
                            phone_require = False
                            code_require = True
                            await msg.answer(f'Вам был отправлен код авторизации Telegram')
                            await msg.answer(f'Введите его в формате: "code<ваш_код>"')
                elif code_require:
                    if len(msg.text) != 9 or 'code' not in msg.text:
                        await msg.answer('Код был введён в неправильном формате')
                    else:
                        code = msg.text.split('code')[1]
                        if not code.isdigit():
                            await msg.answer('Код не является числом')
                        else:
                            try:
                                await msg.answer('Проверка кода')
                                dp.loop.create_task(registration.sing_in(phone, code))
                            except Exception as error:
                                await msg.answer('Телеграм не принимает код')
                                print(error)
                            else:
                                del client
                                client = registration.get_client()
                                code_require = False

                                dp.loop.create_task(scheduled_actions())

                                await msg.answer('Авторизация прошла успешно')
                elif channel_name_require:
                    res = await msg_error_handler(msg, 'channel_name_require', channels_list)
                    print(res)
                    if res:
                        return

                    try:
                        id = int(msg.text.split('(')[-1].strip(')'))
                    except Exception:
                        await msg.answer('Ошибка формата.\nИспользуйте кнопки')
                        return

                    if id in [el.id for el in analyzing_channels_list]:
                        await msg.answer('Канал уже анализируется')
                        return

                    index = [el.id for el in channels_list].index(id)
                    analyzing_channels_list.append(channels_list[index])
                    result = await client(GetFullChannelRequest(channels_list[index].id))

                    await do_record(result)
                    await msg.answer(f'Добавлен канал: {msg.text.split("(")[0]}',
                                     reply_markup=types.ReplyKeyboardRemove())
                    channel_name_require = False
                elif channel_name_for_analyze_require:
                    res = await msg_error_handler(msg, 'channel_name_for_analyze_require')
                    if res:
                        return

                    result = await get_channel_info_from_msg(msg)

                    text = get_current_info(result)
                    await msg.answer(f'Информация о "{result.chats[0].title}":\n{text}',
                                     reply_markup=types.ReplyKeyboardRemove())
                    channel_name_for_analyze_require = False
                elif channel_name_for_delete_require:
                    res = await msg_error_handler(msg, 'channel_name_for_delete_require')
                    if res:
                        return

                    result = await get_channel_info_from_msg(msg)
                    type(result)

                    text = get_current_info(result)
                    await msg.answer(f'Информация о "{result.chats[0].title}":\n{text}',
                                     reply_markup=types.ReplyKeyboardRemove())

                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=True)
                    items = [
                        types.KeyboardButton('Да'),
                        types.KeyboardButton('Нет')
                    ]
                    markup.add(*items)

                    await msg.answer('Вы точно хотите удалить все данные связанные с этим каналом?',
                                     reply_markup=markup)

                    channel_name_for_delete_require = False
                    confirm_for_delete_require = True
                    channel_id_for_delete = result.full_chat.id
                elif confirm_for_delete_require:
                    if msg.text.lower() == 'да':
                        await msg.answer(f'Начинаю удаление канала (id={channel_id_for_delete})',
                                         reply_markup=types.ReplyKeyboardRemove())
                        await delete_data(channel_id_for_delete, True, True)
                        index = [el.id for el in analyzing_channels_list].index(channel_id_for_delete)
                        del analyzing_channels_list[index]
                        await msg.answer(f'Данные удалены')
                    else:
                        await msg.answer('Отмена', reply_markup=types.ReplyKeyboardRemove())

    else:
        if configs['OWNER_ID'] is None:
            if configs['SECRET_KEY'] == msg.text:
                set_config('OWNER_ID', msg.chat.id)
                configs = load_configs()
                await msg.answer('Ключ совпал')
                wait_for_secret_key = []
                await msg.answer('Чтобы продолжить работу введите команду /login')
            else:
                await msg.answer('Ключ не совпал')
        else:
            await msg.answer('Доступ закрыт')


if __name__ == '__main__':
    executor.start_polling(dp)
