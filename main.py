from aiogram import Bot, types, Dispatcher, executor
from cfg_loader import *
import registration
from handle_phone_number import check_phone_number

configs = load_configs()

bot = Bot(token=configs['TOKEN'])
dp = Dispatcher(bot)
wait_for_secret_key = []
client = registration.get_client()
phone_require = False
phone = ''
code_require = False
code = 0

bot.send_message(455713776, 'Бот запущен')


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


@dp.message_handler(commands=['list_channels'])
async def list_channels_handle(msg: types.Message):
    global client

    if not await client.is_user_authorized():
        await msg.answer('Не авторизован')
        try:
            await msg.answer(f'{list(client.iter_dialogs())}')
        except Exception as error:
            print(error)
    else:
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                await msg.answer(dialog.name)


@dp.message_handler(content_types=['text'])
async def text_handle(msg: types.Message):
    global wait_for_secret_key
    global configs
    global phone
    global phone_require
    global code
    global code_require
    global client

    if msg.chat.id not in wait_for_secret_key:
        if configs['OWNER_ID'] is None:
            await msg.answer('Вы не начали работу')
            return
        else:
            if msg.chat.id != configs['OWNER_ID']:
                await msg.answer('Доступ закрыт')
                return
            else:

                if phone_require:
                    try:
                        phone = check_phone_number(msg.text)
                    except ValueError as error:
                        await msg.answer(f'Неверный формат номер телефона: {str(error)}')
                        return
                    else:
                        await msg.answer(f'Ваш номер: {phone}')
                        try:
                            dp.loop.create_task(registration.send_code(phone))
                        except Exception as error:
                            await msg.answer('Телеграм не принимает этот телефон')
                            print(error)
                            return
                        else:
                            phone_require = False
                            code_require = True
                            await msg.answer(f'Вам был отправлен код авторизации Telegram')
                            await msg.answer(f'Введите его в формате: "code<ваш_код>"')
                            return
                elif code_require:
                    if len(msg.text) != 9 or 'code' not in msg.text:
                        await msg.answer('Код был введён в неправильном формате')
                        return
                    else:
                        code = msg.text.split('code')[1]
                        if not code.isdigit():
                            await msg.answer('Код не является числом')
                            return
                        else:
                            try:
                                await msg.answer('Проверка кода')
                                dp.loop.create_task(registration.sing_in(phone, code))
                            except Exception as error:
                                await msg.answer('Телеграм не принимает код')
                                print(error)
                                return
                            else:
                                client = registration.get_client()
                                code_require = False
                                await msg.answer('Авторизация прошла успешно')
                                return

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
