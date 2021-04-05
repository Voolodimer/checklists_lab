from telebot import types
import telebot
import requests

TOKEN = '1600099119:AAGdPs2MBwuvHVTlEmGbslouTcNOt7txtxs'
bot = telebot.TeleBot(TOKEN, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markupinline = types.InlineKeyboardMarkup()
    inlitem = types.InlineKeyboardButton(text='dsf', callback_data='tef')
    itembtn1 = types.KeyboardButton(text='Чек-лист реактора перед засыпкой')
    itembtn2 = types.KeyboardButton('Чек-лист реактора перед ПИ')
    itembtn3 = types.KeyboardButton('Чек-лист реактора перед запуском')
    itembtn4 = types.KeyboardButton('Чек-лист реактора на остановку опыта')
    itembtn5 = types.KeyboardButton('Чек-лист реактора во время режима')
    itembtn6 = types.KeyboardButton('Разрешение на запуск')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    markupinline.add(inlitem)
    bot.send_message(message.chat.id, "ВЫБЕРИТЕ КНОПКУ", reply_markup=markup)
    bot.send_message(message.chat.id, "ВЫБЕРИТЕ КНОПКУ2", reply_markup=markupinline)


def read_questions_file(file_name):
    file = open(file_name, "r", encoding='utf-8')
    questions = file.read().split('\n')
    print(questions)


# Обычный режим
@bot.message_handler(content_types=["text"])
def any_msg(message):
    NameLastName = ''
    name_of_plant = ''
    number_of_exp = ''
    keyboard = types.InlineKeyboardMarkup()
    callback_button = types.InlineKeyboardButton(text="Нажми меня", callback_data="tef")
    keyboard.add(callback_button)
    bot.send_message(message.chat.id, "Я – сообщение из обычного режима", reply_markup=keyboard)

    if message.text == 'Чек-лист реактора перед засыпкой':
        read_questions_file('Чек-лист реактора перед засыпкой.csv')
        bot.send_message(message.chat.id, "Введите своё ФИО")
        # bot.send_message(message.chat.id, "Введите название установки")
        # bot.send_message(message.chat.id, "Введите № опыта")
        # Ввод ФИО, номера установки и № Опыта


# В большинстве случаев целесообразно разбить этот хэндлер на несколько маленьких
@bot.callback_query_handler(func=lambda call:True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        if call.data == "tef":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="ответ")


bot.polling(none_stop=True)