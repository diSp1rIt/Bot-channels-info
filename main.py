from aiogram import Bot, types, Dispatcher, executor
from cfg_loader import *
import registration
from handle_phone_number import check_phone_number
from telethon.tl.functions.channels import GetFullChannelRequest

configs = load_configs()

# ------ Global variables ------
bot = Bot(token=configs['TOKEN'])
dp = Dispatcher(bot)
client = registration.get_client()
channels_list = []
analyzing_channels_list = []
# ------------------------------

# ------ Flags ------
phone_require = False
code_require = False
channel_name_require = False
channel_name_for_analyze_require = False
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
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            if dialog.id not in [elem.id for elem in analyzing_channels_list]:
                text.append(dialog.name + '\n' + Error + f'Не анализируется')
            else:
                text.append(dialog.name + '\n' + Done + f'Анализируется')
            if dialog not in channels_list:
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
    temp_list = list(set(channels_list) - set(analyzing_channels_list))
    items.extend([types.KeyboardButton(elem.name) for elem in temp_list])
    markup.add(*items)
    channel_name_require = True
    await msg.answer('Выберете канал', reply_markup=markup)


@dp.message_handler(commands=['get_info'])
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

    await msg.answer('Просмотр данных')
    if len(analyzing_channels_list) == 0:
        await msg.answer('Список анализируемых каналов пустой')
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        items = [types.KeyboardButton('/cancel')]
        items.extend(
            [types.KeyboardButton(f'{channel.name}') for channel in analyzing_channels_list])
        markup.add(*items)
        await msg.answer('Выберете канал для получения информации', reply_markup=markup)
        channel_name_for_analyze_require = True


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
        text.append(Info + channel.name)
    await msg.answer('\n\n'.join(text))


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
                                client = registration.get_client()
                                code_require = False
                                await msg.answer('Авторизация прошла успешно')
                elif channel_name_require:
                    if msg.text == '/cancel':
                        await msg.answer('Отмена', reply_markup=types.ReplyKeyboardRemove())
                        channel_name_require = False
                        return
                    index = [el.name for el in channels_list].index(msg.text)
                    analyzing_channels_list.append(channels_list[index])
                    await msg.answer(f'Добавлен канал: {msg.text}',
                                     reply_markup=types.ReplyKeyboardRemove())
                    channel_name_require = False
                elif channel_name_for_analyze_require:
                    if msg.text == '/cancel':
                        await msg.answer('Отмена', reply_markup=types.ReplyKeyboardRemove())
                        channel_name_for_analyze_require = False
                        return
                    index = [el.name for el in analyzing_channels_list].index(msg.text)
                    channel = analyzing_channels_list[index]

                    res = await client(GetFullChannelRequest(channel.id))
                    await msg.answer(f'Инфо о {channel.name} канал:\n{res.stringify()}',
                                     reply_markup=types.ReplyKeyboardRemove())
                    channel_name_for_analyze_require = False
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
