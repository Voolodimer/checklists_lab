import pickle
from enum import Enum
import telebot
import time
from telebot import types
import os
from datetime import datetime
import gspread_test
from vedis import Vedis

# тестовые структуры
data_to_write = {}
questions = []
dir = os.getcwd()
global checklist_name

# работа с базой данных состояний (положение пользователя в диалоге)
db_file = "database.vdb"
db_names = 'databasenames.vdb'


class States(Enum):
    S_START = "0"  # Начало нового диалога
    S_STATE = "1"
    S_START_CHECK = "2"
    S_GET_NAME = "3"


with open('users.pickle', 'rb') as f:
    users = pickle.load(f)

with open('config.pickle', 'rb') as f:
    config = pickle.load(f)

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


class User:
    count = 0
    time = ''
    checklist = ''

    def __init__(self, name):
        self.name = name


def send_telegram(path):
    # url = "https://api.telegram.org/bot"
    # url += token
    # method_url = url + "/sendMessage"
    path += '\\'
    chat_id = config['PILOT_PLANT_ID']
    media = os.listdir(path)
    print(media)

    try:
        bot.send_media_group(chat_id, [telebot.types.InputMediaDocument(open(path + photo, 'rb')) for photo in media if
                                       photo.endswith('png') or photo.endswith('jpg')])
    except Exception as e:
        print(e)


def get_start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton(text='Чек-лист реактора перед засыпкой')
    itembtn2 = types.KeyboardButton('Чек-лист реактора перед пи')
    itembtn3 = types.KeyboardButton('Чек-лист реактора перед запуском')
    itembtn4 = types.KeyboardButton('Чек-лист реактора на остановку опыта')
    itembtn5 = types.KeyboardButton('Чек-лист реактора во время режима')
    itembtn6 = types.KeyboardButton('Разрешение на запуск')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    bot.send_message(message.chat.id, "Выберите чек-лист", reply_markup=markup)

# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
                         "{0} Добро пожаловать  в телеграм-бот чек-листы лаборатории! Вы не зарегистрированы. "
                         "Отправьте команду \'/register password\', где вместо password необходимо ввести пароль."
                         .format(message.from_user.first_name)
                         )
        return
    else:
        bot.send_message(message.from_user.id, "{0} добро пожаловать  в телеграм-бот чек-листы лаборатории!\n"
                                               "Для справки по доступным командам отправьте /help в чат."
                         .format(message.from_user.first_name))
        set_state(message.from_user.id, States.S_START_CHECK.value)


@bot.message_handler(commands=['reset'])
def any_msg(message):
    get_start(message)


@bot.message_handler(commands=['register'])
def register_user(message):
    set_state(message.from_user.id, States.S_START.value)
    global users
    arg = message.text.split(' ')[-1]
    # print("arg " + arg)
    if len(arg) != 0 and arg == config['REG_PASSWORD']:
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


@bot.message_handler(commands=['help'])
def help(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
                         "Вы не зарегистрированы. "
                         "Отправьте команду \'/register password\', где вместо password необходимо ввести пароль")
        return
    else:
        bot.send_message(message.from_user.id, '/register - команда для регистрации пользователя для доступа к '
                                               'чек-листам\n'
                                               'Пример ввода: \'/register password\', где password - внутренний пароль' 
                                               '\n'
                                               '/reset - команда перезагрузки бота '
                                               'в случае возникновения ошибок или сбоев')

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
    global checklist_name
    checklist_name = message.text
    if message.text in read_questions_file('buttons.csv'):
        global data_to_write
        data_to_write = {}

        User.checklist = message.text
        timestamp = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M")
        User.time = timestamp
        data_to_write['Время'] = timestamp

        # bot.send_message(message.chat.id, timestamp)
        global questions
        questions = read_questions_file(message.text + '.csv')
        msg = bot.reply_to(message, """\
        Ввведите ваше ФИО
        """)
        # bot.send_message(message.chat.id, msg)
        bot.register_next_step_handler(msg, process_name_step)


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # строим путь и создаём директорию для сохранения фото
        create_dir = dir + '\\' + data_to_write['Введите название установки'] + '\\' + \
              data_to_write['Введите № опыта'] + '\\' + checklist_name
        if not os.path.exists(create_dir):
            os.makedirs(create_dir)


        src = create_dir + '\\' + message.document.file_name
        # print(src)
        # bot.send_message(message.chat.id, src)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
    except Exception as e:
        data_to_write[questions[User.count]] = 'Нет'
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
            global create_dir
            create_dir = dir + '\\' + data_to_write['Введите название установки'] + '\\' + \
                         data_to_write['Введите № опыта'] + '\\' + checklist_name
            if not os.path.exists(create_dir):
                os.makedirs(create_dir)
            # bot.send_message(message.chat.id, len(message.photo))
            file_info = bot.get_file(message.document.file_id)
            src = create_dir + '\\' + message.document.file_name

            # bot.send_message(message.chat.id, src)
            downloaded_files = bot.download_file(file_info.file_path)
            # print(downloaded_files)
            with open(src, 'wb') as new_file:
                new_file.write(downloaded_files)
        except Exception as e:
            pass

        keyboard = types.ReplyKeyboardMarkup(True)
        callback_button1 = types.KeyboardButton(text='Да')
        callback_button2 = types.KeyboardButton(text='Нет')

        if User.count >= 2:
            keyboard.add(callback_button1, callback_button2)

        data_to_write[questions[User.count]] = message.text

        if message.document:
            data_to_write[questions[User.count]] = 'Да'
        User.count += 1

        if User.count >= len(questions):
            # вносим данные в гугл таблицу
            gspread_test.write_googlesheets(User.checklist, data_to_write)
            test_print(data_to_write)

        msg = bot.reply_to(message, questions[User.count], reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_name_step)

    except Exception as e:
        bot.send_message(message.chat.id, 'Чек-лист сохранён на гугл диск '
                                          'https://docs.google.com/spreadsheets/d/'
                                          '1-W9NVryCMOYXNZAnNWvWVIeswHt_N4THIAAyMoHDQGs/edit?ts=605d99a4#gid=0')
        User.count = 0
        User.time = ''
        send_telegram(create_dir)
        get_start(message)



def test_print(message):
    with open('out.txt', 'w', encoding='utf-8') as out:
        for key, val in message.items():
            out.write('{}:{}\n'.format(key, val))


while True:
    try:
        # Данная функция запускает бесконечный опрос телеграм-бота на наличие входящих запросов
        bot.polling()
    except BaseException as ex:
        time.sleep(5)
        print("Произошла ошибка, бот был перезапущен!")