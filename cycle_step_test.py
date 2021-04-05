import pickle
from enum import Enum
import telebot
import time
from telebot import types
import os
from datetime import datetime
import gspread_test
from vedis import Vedis

# Удалить токен!
# API_TOKEN = '1600099119:AAGdPs2MBwuvHVTlEmGbslouTcNOt7txtxs'


# тестовые структуры
user_dict = {}
before_backfill = {}
test_datas = []
dir = os.getcwd()

# работа с базой данных состояний (положение пользователя в диалоге)
db_file = "database.vdb"
db_names = 'databasenames.vdb'

class States(Enum):
    S_START = "0"  # Начало нового диалога
    S_CHOOSE = "1"
    S_START_CHECK = "2"
    S_GET_NAME = "3"
# data = {'BOT_TOKEN':'1600099119:AAGdPs2MBwuvHVTlEmGbslouTcNOt7txtxs',
#         'DOCUMENT_ID': '1agrCBLZTYY1NRRQk4wWkoD4iC4bbQ4StqCGOqmt9TgU'}
# with open('config.pickle', 'wb') as f:
#     pickle.dump(data, f)




# data_u = []
# with open('users.pickle', 'wb') as f:
#     users = pickle.dump(data_u, f)
with open('users.pickle', 'rb') as f:
    users = pickle.load(f)

with open('config.pickle', 'rb') as f:
    config = pickle.load(f)

print(users)
# print(config['BOT_TOKEN'])

# подключение к боту. Токен берём из файла config
bot = telebot.TeleBot(config['BOT_TOKEN'])


# функция чтения файла с вопросами
def read_questions_file(file_name):
    with open(file_name, "r", encoding='utf-8') as file:
        return file.read().split('\n')


# функция получения из базы «состояния» пользователя
def get_current_state(user_id):
    with Vedis(db_file) as db:
        try:
            return db[user_id].decode()
        except KeyError:
            # при ошибке значение по умолчанию - начало диалога
            print("ошибка ключа get_curr_state")
            return States.S_START.value


def set_name(user_id, value):
    with Vedis(db_names) as db:
        try:
            db[user_id] = value
            return True
        except:
            print('Ошибка сохранения фамилии')
            return False


# функция сохранения «состояния» пользователя в нашу базу
def set_state(user_id, value):
    with Vedis(db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            return False


# получаем имя пользователя из базы данных
def get_name(user_id):
    # print(user_id, end=' ')
    with Vedis(db_names) as db:
        try:
            return db[user_id]
        except KeyError:
            print('ошибка ключа')
            return None
            # if get_current_state(user_id) != States.S_START.value:
            #     return str(user_id)



questions = read_questions_file('Чек-лист реактора перед засыпкой.csv')
len_before = len(questions)


class User:
    count = 0
    time = ''
    checklist = ''

    def __init__(self, name):
        self.name = name


# Handle '/start' and '/help'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
            "{0} Добро пожаловать  в телеграм-бот чек-листы лаборатории! Вы не зарегистрированы. "
            "Отправьте команду /register password, где вместо password необходимо ввести пароль."
                         .format(message.from_user.first_name)
        )
        return
    else:
        bot.send_message(message.from_user.id, "{0} добро пожаловать  в телеграм-бот чек-листы лаборатории!"
                                               " Для справки по доступным командам отправьте /help в чат."
                         .format(message.from_user.first_name))
        set_state(message.from_user.id, States.S_START_CHECK.value)


def get_start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton(text='Чек-лист реактора перед засыпкой')
    itembtn2 = types.KeyboardButton('Чек-лист реактора перед ПИ')
    itembtn3 = types.KeyboardButton('Чек-лист реактора перед запуском')
    itembtn4 = types.KeyboardButton('Чек-лист реактора на остановку опыта')
    itembtn5 = types.KeyboardButton('Чек-лист реактора во время режима')
    itembtn6 = types.KeyboardButton('Разрешение на запуск')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    bot.send_message(message.chat.id, "Выберите чек-лист", reply_markup=markup)


@bot.message_handler(commands=['reset'])
def any_msg(message):
    get_start(message)



@bot.message_handler(commands=['register'])
def register_user(message):
    set_state(message.from_user.id, States.S_START.value)
    global users
    arg = message.text.split(' ')[-1]
    # print("arg " + arg)
    if len(arg) != 0 and arg == 'rrtrrtrrt':
        if users.count(message.from_user.id) != 0:
            bot.send_message(message.from_user.id, 'Вы уже зарегистрированы')
        else:
            users.append(message.from_user.id)
            with open('users.pickle', 'wb') as f:
                pickle.dump(users, f)
            bot.send_message(message.from_user.id,
                             'Пользователь {0} с id = {1} зарегистрирован.'
                             .format(message.from_user.first_name, message.from_user.id))
            first_name = get_name(message.from_user.id)
            if first_name is None:
                bot.send_message(message.from_user.id,
                                 '''Введите свою фамилию (будет использоваться в графе "ФИО" на гугл диске)''')
                set_state(message.from_user.id, States.S_GET_NAME.value)
    else:
        bot.send_message(message.from_user.id, 'Пароль не верный')


@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_GET_NAME.value)
def get_name_to_db(message):
    name = message.text
    set_name(message.from_user.id, name)
    bot.send_message(message.from_user.id, 'Фамилия сохранена')
    set_state(message.from_user.id, States.S_START_CHECK.value)
    get_start(message)


@bot.message_handler(content_types=["text"],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_START_CHECK.value)
def any_msg(message):
    if message.text == 'Чек-лист реактора перед засыпкой':
        User.checklist = message.text
        timestamp = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M")
        User.time = timestamp
        before_backfill['Время'] = timestamp

        #bot.send_message(message.chat.id, timestamp)
        read_questions_file('Чек-лист реактора перед засыпкой.csv')
        msg = bot.reply_to(message, """\
        Ввведите ваше ФИО
        """)
        #bot.send_message(message.chat.id, msg)
        bot.register_next_step_handler(msg, process_name_step)


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = dir + '\\' + before_backfill['Введите название установки'] + '\\' + \
              before_backfill['Введите № опыта'] + message.document.file_name
        print(src)
        # bot.send_message(message.chat.id, src)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        # bot.reply_to(message, "Пожалуй, я сохраню это")
    except Exception as e:
        bot.reply_to(message, e)


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    try:
        chat_id = message.chat.id
        file_info = bot.get_file(message.photo[-1].file_id)
        bot.send_message(message.chat.id, file_info)
        downloaded_file = bot.download_file(file_info.file_path)

        src = dir + '\\' + file_info.file_path.split('/')[-1]
        bot.send_message(message.chat.id, src)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

    except Exception as e:
        bot.reply_to(message, e)


def process_name_step(message):
    try:
        try:
            # bot.send_message(message.chat.id, len(message.photo))
            file_info = bot.get_file(message.document.file_id)
            src = dir + '\\' + message.document.file_name

            # bot.send_message(message.chat.id, src)
            downloaded_files = bot.download_file(file_info.file_path)
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_files)
        except Exception as e:
            pass

        keyboard = types.ReplyKeyboardMarkup(True)
        callback_button1 = types.KeyboardButton(text='Да')
        callback_button2 = types.KeyboardButton(text='Нет')
        if User.count >= 2:
            keyboard.add(callback_button1, callback_button2)

        before_backfill[questions[User.count]] = message.text
        # test_datas.append(list(message.text))
        if message.document:
            before_backfill[questions[User.count]] = 'Да'
        User.count += 1
        if User.count >= len(questions):
            # вносим данные в гугл таблицу
            gspread_test.write_googlesheets(User.checklist, before_backfill)
            # gspread_test.write_googlesheets(User.checklist, test_datas)
            test_print(before_backfill)
        msg = bot.reply_to(message, questions[User.count], reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_name_step)

    except Exception as e:
        bot.send_message(message.chat.id, 'Чек-лист сохранён на гугл диск '
                              'https://docs.google.com/spreadsheets/d/'
                              '1-W9NVryCMOYXNZAnNWvWVIeswHt_N4THIAAyMoHDQGs/edit?ts=605d99a4#gid=0')
        # bot.reply_to(message, e)
        User.count = 0
        User.time = ''
        # send_welcome(message)
        get_start(message)


def test_print(message):
    with open('out.txt', 'w', encoding='utf-8') as out:
        for key, val in message.items():
            out.write('{}:{}\n'.format(key, val))

# bot.reply_to(message, 'выход из цикла')
# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
#bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
#bot.load_next_step_handlers()

bot.polling()