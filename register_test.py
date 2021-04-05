import telebot
from telebot import types
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
import pickle
from vedis import Vedis
from enum import Enum
import os
import re
import datetime

# загружаем файл config.pickle с внесенными в него BotID и SheetID
with open('config.pickle', 'rb') as f:
    config = pickle.load(f)

# загружаем файл users.pickle с id пользователей
with open('users.pickle', 'rb') as f:
    users = pickle.load(f)

print(config)

# авторизация/подключения к таблице Google,
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sh = client.open_by_key(config['DOCUMENT_ID'])

# авторизация на Google-диске
gauth = GoogleAuth()
drive = GoogleDrive(gauth)

# подключение к боту
botID = config['BOT_TOKEN']
bot = telebot.TeleBot(botID)

# работа с базой данных состояний (положение пользователя в диалоге)
db_file = "database.vdb"
db_names = 'databasenames.vdb'

class States(Enum):
    S_START = "0"  # Начало нового диалога
    S_CHOOSE = "1"
    S_ENTER_ID = "2"
    S_ADD = "3"
    S_CHANGE_POS = '4'
    S_CHANGE_VOL = '5'
    S_DEL = '6'
    S_ADD1 = '7'
    S_ADD2 = '8'
    S_ADD3 = '9'
    S_GET_NAME = '10'


# функция получения из базы «состояния» пользователя
def get_current_state(user_id):
    with Vedis(db_file) as db:
        try:
            return db[user_id]
        except KeyError:  # Если такого ключа почему-то не оказалось
            return States.S_START.value  # значение по умолчанию - начало диалога


# функция сохранения «состояния» пользователя в нашу базу
def set_state(user_id, value):
    with Vedis(db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            # тут желательно как-то обработать ситуацию
            return False

def set_name(user_id, value):
    with Vedis(db_names) as db:
        try:
            db[user_id] = value
            return True
        except:
            print('Ошибка сохранения фамилии')  # тут желательно как-то обработать ситуацию
            return False

def get_name(user_id):
    with Vedis(db_names) as db:
        try:
            return db[user_id]
        except KeyError:  # Если такого ключа почему-то не оказалось
            if get_current_state(user_id) != States.S_START.value:
                return str(user_id)


print('Программа запущена.')

@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_GET_NAME.value)
def get_name_to_db(message):
    name = message.text
    set_name(message.from_user.id, name)
    bot.send_message(message.from_user.id, 'Фамилия сохранена в местном файле базы данных.')
    set_state(message.from_user.id, States.S_START.value)


# обработчики команд /start, /help, /register
@bot.message_handler(commands=['start'])
def start(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
                         "Добро пожаловать в телеграм-бот учета ЛВЖ! Вы не зарегистрированы. "
                         "Отправьте команду /register password, где вместо password необходимо ввести пароль.")
        return
    else:
        bot.send_message(message.from_user.id, 'Добро пожаловать в телеграм-бот учета ЛВЖ! '
                                               'Для справки по доступным командам отправьте /help в чат.')
        set_state(message.from_user.id, States.S_START)


@bot.message_handler(commands=['help'])
def help(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
                         "Вы не зарегистрированы. "
                         "Отправьте команду /register password, где вместо password необходимо ввести пароль")
        return
    else:
        bot.send_message(message.from_user.id, '/find_id - Нахождение информации о емкости по индивидуальному номеру, '
                                               'внесение изменений в google-таблицу (перенос емкости в другое место, '
                                               'переливание, расход и т.д.)\n'
                                               '/add - Присвоить новому продукту ID и внести в журнал учета.')


@bot.message_handler(commands=['register'])
def register_user(message):
    set_state(message.from_user.id, States.S_START.value)
    global users
    arg = message.text.split(' ')[-1]
    if len(arg) != 0 and arg == 'rrtrrtrrt':
        if users.count(message.from_user.id) != 0:
            bot.send_message(message.from_user.id, 'Вы уже зарегистрированы')
        else:
            users.append(message.from_user.id)
            with open('users.pickle', 'wb') as f:
                pickle.dump(users, f)
            bot.send_message(message.from_user.id,
                             'Пользователь с id = {0} зарегистрирован.'.format(message.from_user.id))
            name1 = get_name(message.from_user.id)
            if name1 is None:
                bot.send_message(message.from_user.id,
                                 'Введите свою фамилию (будет использоваться в графе "ФИО/Дата ревизии" '
                                 'электронного журнала):')
                set_state(message.from_user.id, States.S_GET_NAME.value)
    else:
        bot.send_message(message.from_user.id, 'Пароль не верный')


# клавиатура выбора типа емкости

choose_type = types.InlineKeyboardMarkup()
button_bottle = types.InlineKeyboardButton(text='Бутылка', callback_data='бутылка')
button_can = types.InlineKeyboardButton(text='Канистра', callback_data='канистра')
button_barrel = types.InlineKeyboardButton(text='Бочка', callback_data='бочка')
button_c6 = types.InlineKeyboardButton(text='Гексан/гептан', callback_data='гексан')
choose_type.add(button_bottle)
choose_type.add(button_can, button_barrel)
choose_type.add(button_c6)


# обработчик команды /find_id
@bot.message_handler(commands=['find_id'])
def find_id(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
                         "Вы не зарегистрированы. "
                         "Отправьте команду /register password, где вместо password необходимо ввести пароль")
        return
    bot.send_message(message.from_user.id, 'Укажите тип емкости:', reply_markup=choose_type)
    set_state(message.from_user.id, States.S_CHOOSE.value)


# клавиатура и кнопки действий с продуктом
vessel_action = types.InlineKeyboardMarkup()
change_pos = types.InlineKeyboardButton(text='Изменить расположение', callback_data='расположение')
change_vol = types.InlineKeyboardButton(text='Изменить объем', callback_data='объем')
vessel_del = types.InlineKeyboardButton(text='Перенести в архив (продукт потрачен)', callback_data='потрачено')
vessel_action.add(change_pos)
vessel_action.add(change_vol)
vessel_action.add(vessel_del)

# клава ок/назад, используется в случаях изменения чего-либо для емкостей
new = types.InlineKeyboardMarkup()
new1 = types.InlineKeyboardMarkup()
new_ok = types.InlineKeyboardButton(text='Да', callback_data='ok')
new_back = types.InlineKeyboardButton(text='Назад', callback_data='back')
new.add(new_back)
new1.add(new_ok, new_back)


# обработчик нажатия встроенных кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global wks, new_row, new_id
    if call.message:
        if call.data == 'бутылка':
            wks = sh.worksheet('Бутылки')
            if get_current_state(call.message.chat.id) == States.S_ADD.value:
                id_list = wks.col_values(1)
                id_list.pop(0)
                id_list = filter(None, id_list)
                id_list2 = [int(x) for x in id_list]
                new_id = int(max(id_list2)) + 1
                text_new_id = 'Емкости присвоен ID: ' + str(new_id) + '. Укажите его на этикетке. Введите название ' \
                                                                      'продукта (в скобках также укажите объем бочки):'
                bot.send_message(call.message.chat.id, text_new_id)
                new_row = len(wks.col_values(2)) + 1
                wks.update_cell(new_row, 1, new_id)
                set_state(call.message.chat.id, States.S_ADD1.value)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Введите номер (ID) бутылки/реактива:')
                set_state(call.message.chat.id, States.S_ENTER_ID.value)
        elif call.data == 'канистра':
            wks = sh.worksheet('Канистры')
            if get_current_state(call.message.chat.id) == States.S_ADD.value:
                id_list = wks.col_values(1)
                id_list.pop(0)
                id_list = filter(None, id_list)
                id_list2 = [int(x) for x in id_list]
                new_id = int(max(id_list2)) + 1
                text_new_id = 'Емкости присвоен ID: ' + str(new_id) + '. Укажите его на этикетке. Введите название ' \
                                                                      'продукта (в скобках также укажите объем тары):'
                bot.send_message(call.message.chat.id, text_new_id)
                new_row = len(wks.col_values(2)) + 1
                wks.update_cell(new_row, 1, new_id)
                set_state(call.message.chat.id, States.S_ADD1.value)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Введите номер (ID) канистры:')
                set_state(call.message.chat.id, States.S_ENTER_ID.value)
        elif call.data == 'бочка':
            wks = sh.worksheet('Бочки')
            if get_current_state(call.message.chat.id) == States.S_ADD.value:
                id_list = wks.col_values(1)
                id_list.pop(0)
                id_list = filter(None, id_list)
                id_list2 = [int(x) for x in id_list]
                new_id = int(max(id_list2)) + 1
                text_new_id = 'Емкости присвоен ID: ' + str(new_id) + '. Укажите его на этикетке. Введите название ' \
                                                                      'продукта:'
                bot.send_message(call.message.chat.id, text_new_id)
                new_row = len(wks.col_values(2)) + 1
                wks.update_cell(new_row, 1, new_id)
                set_state(call.message.chat.id, States.S_ADD1.value)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Введите номер (ID) бочки:')
                set_state(call.message.chat.id, States.S_ENTER_ID.value)
        elif call.data == 'гексан':
            wks = sh.worksheet('Гексан, гептан')
            if get_current_state(call.message.chat.id) == States.S_ADD.value:
                id_list = wks.col_values(1)
                id_list.pop(0)
                id_list = filter(None, id_list)
                id_list2 = [int(x) for x in id_list]
                new_id = int(max(id_list2)) + 1
                text_new_id = 'Емкости присвоен ID: ' + str(new_id) + '. Укажите его на этикетке. Введите название ' \
                                                                          'продукта (напр. "Гексан ХЧ, Вектон"):'
                bot.send_message(call.message.chat.id, text_new_id)
                new_row = len(wks.col_values(2)) + 1
                wks.update_cell(new_row, 1, new_id)
                set_state(call.message.chat.id, States.S_ADD1.value)
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Введите номер (ID) тары:')
                set_state(call.message.chat.id, States.S_ENTER_ID.value)
        elif call.data == 'хроматограмма':
            if criteria_chrom.search(chrom):
                try:
                    chrom_id_split = chrom.split('id=')
                except:
                    bot.send_message(call.message.chat.id, 'В журнале учета ссылка указана в неверном формате.')
                else:
                    chrom_id = chrom_id_split[1]
                    gdrive_file = drive.CreateFile({'id': chrom_id})
                    gdrive_file.FetchMetadata()
                    gdrive_file.GetContentFile(gdrive_file['title'])
                    kitty = open(gdrive_file['title'], 'rb')
                    bot.send_document(chat_id=call.message.chat.id, data=kitty)
                    kitty.close()
                    os.remove(gdrive_file['title'])
        elif call.data == 'изменения':
            bot.send_message(call.message.chat.id, 'Какие изменения необходимо внести?', reply_markup=vessel_action)
        elif call.data == 'расположение':
            set_state(call.message.chat.id, States.S_CHANGE_POS.value)
            bot.send_message(call.message.chat.id, 'Введите новое расположение:')
        elif call.data == 'объем':
            set_state(call.message.chat.id, States.S_CHANGE_VOL.value)
            bot.send_message(call.message.chat.id, 'Введите новое значение объема (число) в литрах:')
        elif call.data == 'потрачено':
            set_state(call.message.chat.id, States.S_DEL.value)
            bot.send_message(call.message.chat.id, 'Нажмите "Да" для переноса данного продукта в архив.',
                             reply_markup=new1)
        elif call.data == 'back':
            set_state(call.message.chat.id, States.S_ENTER_ID.value)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Какие изменения необходимо внести?', reply_markup=vessel_action)
        elif call.data == 'ok':
            if get_current_state(call.message.chat.id) == States.S_DEL.value:
                try:
                    wks
                except:
                    bot.send_message(call.message.chat.id, 'Все стоит начать сначала. \n/find_id, чтобы указать '
                                                           'тип тары;\n/help - список функций.')
                else:
                    row_to_copy = wks.row_values(id_row)
                    archive = sh.worksheet('Архив').col_values(1)
                    end_archive = len(archive) + 1
                    for i in range(len(row_to_copy)):
                        sh.worksheet("Архив").update_cell(end_archive, i + 1, row_to_copy[i])
                    wks.delete_row(id_row)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text='Данные по продукту перенесены в архив.')
                    name = get_name(call.message.chat.id)
                    wks = sh.worksheet("Архив")
                    now = datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')
                    fio = name + '/' + now
                    fio_header = wks.find("ФИО/Дата ревизии")
                    wks.update_cell(end_archive, fio_header.col, fio)
                    set_state(call.message.chat.id, States.S_ENTER_ID.value)


@bot.message_handler(commands=['add'])
def add(message):
    if users.count(message.from_user.id) == 0:
        bot.send_message(message.from_user.id,
                         "Вы не зарегистрированы. "
                         "Отправьте команду /register password, где вместо password необходимо ввести пароль.")
        return
    bot.send_message(message.from_user.id, 'Укажите тип емкости:', reply_markup=choose_type)
    set_state(message.from_user.id, States.S_ADD.value)


@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_ADD1.value)
def new_vessel(message):
    nazv_header = wks.find("Название")
    wks.update_cell(new_row, nazv_header.col, message.text)
    bot.send_message(message.from_user.id, 'Введите объем (число) в литрах:')
    set_state(message.from_user.id, States.S_ADD2.value)


@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_ADD2.value)
def new_vessel(message):
    try:
        float(message.text)
    except:
        bot.send_message(message.from_user.id, "Неверный формат, необходимо ввести число. Дробную часть указывайте "
                                               "через точку.")
    else:
        new_vol = message.text
        new_vol2 = new_vol.replace(".", ",")
        volume_header = wks.find("Объем, л")
        wks.update_cell(new_row, volume_header.col, new_vol2)
        bot.send_message(message.from_user.id, 'Введите расположение емкости:')
        set_state(message.from_user.id, States.S_ADD3.value)


@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_ADD3.value)
def new_vessel(message):
    place_header = wks.find("Расположение")
    wks.update_cell(new_row, place_header.col, message.text)
    name = get_name(message.from_user.id)
    now = datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')
    fio = name + '/' + now
    fio_header = wks.find("ФИО/Дата ревизии")
    wks.update_cell(new_row, fio_header.col, fio)
    bot.send_message(message.from_user.id, 'Данные успешно сохранены.')
    set_state(message.from_user.id, States.S_START.value)


@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_CHANGE_POS.value)
def new_place(message):
    try:
        wks
    except:
        bot.send_message(message.from_user.id, 'Все стоит начать сначала. \n/find_id, чтобы указать тип тары;\n'
                                               '/help - список функций.')
    else:
        wks.update_cell(id_row, place_header.col, message.text)
        name = get_name(message.from_user.id)
        now = datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')
        fio = name + '/' + now
        fio_header = wks.find("ФИО/Дата ревизии")
        wks.update_cell(new_row, fio_header.col, fio)
        bot.send_message(message.from_user.id, 'Расположение изменено.')


@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_CHANGE_VOL.value)
def new_volume(message):
    try:
        wks
    except:
        bot.send_message(message.from_user.id, 'Все стоит начать сначала. \n/find_id, чтобы указать тип тары;\n'
                                               '/help - список функций.')
    else:
        try:
            float(message.text)
        except:
            bot.send_message(message.from_user.id, "Неверный формат, необходимо ввести число. Дробную часть указывайте "
                                                   "через точку.")
        else:
            new_vol = message.text
            new_vol2 = new_vol.replace(".", ",")
            wks.update_cell(id_row, volume_header.col, new_vol2)
            name = get_name(message.from_user.id)
            now = datetime.datetime.now().strftime('%d.%m.%y %H:%M:%S')
            fio = name + '/' + now
            fio_header = wks.find("ФИО/Дата ревизии")
            wks.update_cell(new_row, fio_header.col, fio)
            bot.send_message(message.from_user.id, 'Объем изменен.')


# обработчик сообщений, полученных в состоянии ввода ID продукта
@bot.message_handler(content_types=['text'],
                     func=lambda message: get_current_state(message.from_user.id) == States.S_ENTER_ID.value)
def enter_id(message):
    try:
        wks
    except:
        bot.send_message(message.from_user.id, 'Все стоит начать сначала. \n/find_id, чтобы указать тип тары;\n'
                                               '/help - список функций.')

    else:
        global id_row, nazv_header, volume_header, place_header, chrom_header
        ids_list = wks.col_values(1)
        indices = [i for i, s in enumerate(ids_list) if message.text in s]
        nazv_header = wks.find("Название")
        volume_header = wks.find("Объем, л")
        place_header = wks.find("Расположение")
        chrom_header = wks.find("Хроматограмма")

        if indices:
            id_row = indices[0] + 1
            # if len(indices) == 1:
            #     id_row = indices[0] + 1
            #     # bot.send_message(message.from_user.id, info_mess)
            # else:
            #     id_row = indices[0] + 1
            #     # bot.send_message(message.from_user.id, info_mess)
        else:
            bot.send_message(message.from_user.id, 'Емкости с таким ID не найдено! Введите другой номер, '
                                                   'либо:\n- искать среди другого типа тары (/find_id);\n'
                                                   '- внести информацию по продукту в журнал учета (/add).')
            return
        global volume, place, chrom, criteria_chrom
        nazv = wks.cell(id_row, nazv_header.col).value
        volume = wks.cell(id_row, volume_header.col).value
        place = wks.cell(id_row, place_header.col).value
        chrom = wks.cell(id_row, chrom_header.col).value
        criteria_chrom = re.compile(r'drive.google.com/')

        info_mess = nazv + '\n\n' + 'ID: ' + message.text + '\n' + 'Объем, л: ' + volume + '\n' \
                    + 'Расположение: ' + place

        # кнопочки получения хроматограммы или изменения каких-то параметров емкости в журнале
        set_changes = types.InlineKeyboardMarkup()
        get_chrom_button = types.InlineKeyboardButton(text='Скачать хроматограмму', callback_data='хроматограмма')
        change_button = types.InlineKeyboardButton(text='Внести изменения в журнал', callback_data='изменения')

        if criteria_chrom.search(chrom):
            info_mess = info_mess + '\n' + 'Хроматограмма: да'
            set_changes.add(get_chrom_button)
            set_changes.add(change_button)
        else:
            info_mess = info_mess + '\n' + 'Хроматограмма: нет'
            set_changes.add(change_button)

        bot.send_message(message.from_user.id, info_mess, reply_markup=set_changes)


# if __name__ == '__main__':
#     bot.polling(none_stop=True)

bot.polling()

# while True:
#     try:
#         # Данная функция запускает опрос телеграм-бота на предмет новых сообщений
#         bot.polling()
#         datetime.time.sleep(5)
#     except BaseException as e:
#          print("Произошла ошибка, бот был перезапущен!")
#          print(e)