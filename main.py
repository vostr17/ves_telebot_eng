import random
import os
import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import create_tables, User, DataBaseWords, BotLogger
from db import db_words

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

# Конфигурация из файла .env
load_dotenv()

"""Токен телеграмм-бота"""
BOT_TOKEN = os.getenv('BOT_TOKEN')
"""Имя базы данных PostgreSQL"""
DB_NAME = os.getenv('DB_NAME')
"""Имя пользователя базы данных PostgreSQL"""
DB_USER = os.getenv('DB_USER')
"""Пароль от базы данных PostgreSQL"""
DB_PASSWORD = os.getenv('DB_PASSWORD')
"""HOST для DSN"""
DB_HOST = os.getenv('DB_HOST')
"""Номер порта для DSN"""
DB_PORT = os.getenv('DB_PORT')

# Check TOKEN
if not BOT_TOKEN:
    raise ValueError("Не найден токен бота! Проверьте файл .env")

DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DSN)
create_tables(engine)
bot_logger = BotLogger()



""" Добавление нового пользователя в таблицу user базы данных test"""
def add_user_in_db(name, user_id):

    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter(User.user_id == user_id).one_or_none()
    if not user:
        user_all = User(name=name, user_id=user_id)
        session.add(user_all)
        session.commit()
        session.close()
        return True
    else:
        session.close()
        return False

"""Добавление лога в таблицу bot_logger"""
def add_log(datatime, user_id, rus_word, operation, status):
    Session = sessionmaker(bind=engine)
    session = Session()

    bot_logger = BotLogger(date_time=datatime, user_id=user_id, rus_word=rus_word, operation=operation, status=status)
    session.add(bot_logger)
    session.commit()
    session.close()



"""Возвращает количество слов в базе данных"""
def num_words(uid):
    Session = sessionmaker(bind=engine)
    session = Session()
    num1 = session.query(DataBaseWords).filter(DataBaseWords.user_id == id_uid(uid)).count()
    num2 = session.query(DataBaseWords).filter(DataBaseWords.user_id == 1).count()

    return num1 + num2



""" Добавление нового слова в таблицу db_words базы данных test"""
def add_words_in_db(rus_word, eng_word, user_id):

    Session = sessionmaker(bind=engine)
    session = Session()

    """ Проверка наличия русского слова в базе данных для всех пользователей"""
    russian_word_all = session.query(DataBaseWords).filter(DataBaseWords.rus_word == rus_word, DataBaseWords.user_id == 1).one_or_none()

    """ Проверка наличия русского слова в базе данных для пользователя с текущим uid"""
    u_id = id_uid(user_id)
    russian_word_uid = session.query(DataBaseWords).filter(DataBaseWords.rus_word == rus_word, DataBaseWords.user_id == u_id).one_or_none()

    """ Проверка наличия пользователя в таблице user бд test"""
    uid = session.query(User).filter(User.user_id == user_id).one_or_none()

    if not russian_word_all and not russian_word_uid:
        dbw1 = DataBaseWords(rus_word=rus_word, eng_word=eng_word, user_id=uid.id)
        session.add(dbw1)
        session.commit()
        session.close()
        add_log(datetime.datetime.now(), user_id, rus_word, 'addw', True)
        return f'Слово "{rus_word}" успешно добавлено в базу данных пользователя {name_uid(user_id)}'
    else:
        session.close()
        add_log(datetime.datetime.now(), user_id, rus_word, 'addw', False)
        return f'Слово "{rus_word}" уже существует в базе данных'



""" Удаление слова пользователя user из таблицы db_words базы данных test"""
def del_words_in_db(rus_word, user_id):

    Session = sessionmaker(bind=engine)
    session = Session()
    """ Проверка наличия русского слова в таблице db_words бд test"""
    russian_word = session.query(DataBaseWords).filter(DataBaseWords.rus_word == rus_word).one_or_none()
    """ Проверка наличия пользователя в таблице user бд test"""
    uid = session.query(User).filter(User.user_id == user_id).one_or_none()

    if not russian_word:
        session.close()
        add_log(datetime.datetime.now(), user_id, rus_word, 'delw', False)
        return f'Нельзя удалить слово "{rus_word}", т.к. его нет в базе данных.'
    elif (russian_word.user_id == 1) or (uid.user_id != user_id):
        session.close()
        add_log(datetime.datetime.now(), user_id, rus_word, 'delw', False)
        return f'Нельзя удалить слово "{rus_word}", т.к. оно не принадлежит пользователю {name_uid(user_id)}'
    elif uid.user_id == user_id:
        session.delete(russian_word)
        session.commit()
        session.close()
        add_log(datetime.datetime.now(), user_id, rus_word, 'delw', True)
        return f'Слово "{rus_word}" успешно удалено из базы данных пользователя {name_uid(user_id)}.'
    else:
        session.close()
        add_log(datetime.datetime.now(), user_id, rus_word, 'delw', False)
        return



"""Возвращает случайное слово для изучения"""
def random_target_word(user_id):
    words = []
    Session = sessionmaker(bind=engine)
    session = Session()
    english_word = session.query(DataBaseWords.eng_word).filter(DataBaseWords.user_id == id_uid(user_id)).all()

    for user_word_tuple in english_word:
        words.append(user_word_tuple[0])
    english_word = session.query(DataBaseWords.eng_word).filter(DataBaseWords.user_id == 1).all()
    for user_word_tuple in english_word:
        words.append(user_word_tuple[0])

    session.close()
    return random.choice(words)



"""Возвращает перевод слова"""
def translate_word(eng_word):
    Session = sessionmaker(bind=engine)
    session = Session()

    english_word = session.query(DataBaseWords).filter(DataBaseWords.eng_word == eng_word).one_or_none()
    rus_word = english_word.rus_word
    session.close()
    return rus_word



"""Возвращает n случайных слов для неправильного перевода"""
def random_n_words(target_word, n):
    result = []
    words = []
    i = 0

    Session = sessionmaker(bind=engine)
    session = Session()

    english_word = session.query(DataBaseWords.eng_word).all()

    for word_tuple in english_word:
        words.append(word_tuple[0])
    session.close()

    while i < n:
        word = random.choice(words)
        if word == target_word:
            continue
        if word not in result:
            result.append(word)
            i += 1

    return result



"""Проверяет наличие пользователя в базе данных"""
def is_uid_in_db(uid):
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter(User.user_id == uid).one_or_none()
    if user:
        session.close()
        return True
    else:
        session.close()
        return False


""" Возвращает id в таблице db_words по user_id таблицы user"""
def id_uid(user_id):
    Session = sessionmaker(bind=engine)
    session = Session()
    u_id = session.query(User).filter(User.user_id == user_id).first().id
    session.close()
    return u_id

"""Возвращает имя пользователя по user_id"""
def name_uid(uid):
    Session = sessionmaker(bind=engine)
    session = Session()

    user = session.query(User).filter(User.user_id == uid).one_or_none()
    if user:

        session.close()
        return user.name
    else:
        session.close()
        return False

#Добавление "нулевого" пользователя
add_user_in_db('all', 1)

#Заполнение базы данных слов из файла db.py
for d in db_words:
    add_words_in_db(d['rus_word'], d['eng_word'], 1)


state_storage = StateMemoryStorage()
token_bot = BOT_TOKEN
bot = TeleBot(BOT_TOKEN, state_storage=state_storage)

print('Start telegram bot...')
known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

"""Класс текущего состояния бота"""
class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()



"""Обработка команд /cards и /start"""
@bot.message_handler(commands=['cards', 'start'])
#Приветствие пользователя или запрос имени нового пользователя
def welc_message(message):

    if is_uid_in_db(message.chat.id):
        bot.send_message(message.chat.id, f"Здравия, {name_uid(message.from_user.id)}! \n Давай учить английские слова...")
        create_cards(message)
    else:
        msg = bot.send_message(message.chat.id, f"Здравия, Новый пользователь! Как к тебе обращаться?")
        bot.register_next_step_handler(msg, add_new_username)

#Добавляет в базу данных имя нового пользователя
def add_new_username(message):
    cid = message.chat.id
    add_user_in_db(message.text, cid)
    welc_message(message)

#Функция создания новой карточки
def create_cards(message):
    cid = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    target_word = random_target_word(cid)  # брать из БД
    translate = translate_word(target_word)  # брать из БД
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = random_n_words(target_word, 4) # брать из БД
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others



"""Обработка кнопки NEXT (Дальше)"""
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)



"""Обработка кнопки DELETE_WORD"""
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
#Запрашивает русское слово для удаления
def delete_word(message):
    cid = message.chat.id
    msg = bot.send_message(cid, 'Введите слово, которое хотите удалить:')
    bot.register_next_step_handler(msg, message_reply_del)

#Удаляет слово и выдаёт количество оставшихся слов в базе данных
def message_reply_del(message):
    text = del_words_in_db(message.text, message.chat.id)
    bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, f"В базе данных {num_words(message.chat.id)} слов.")
    create_cards(message)



"""Обработка кнопки ADD_WORD"""
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
#Просит ввести новое слово и перевод
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    msg = bot.send_message(cid, 'Введите слово и перевод через пробел.')
    bot.register_next_step_handler(msg, message_reply_add)

#Добавляет новое слово и выдаёт общее количество слов в базе данных пользователя
def message_reply_add(message):
    text = message.text.split()
    text1 = add_words_in_db(text[0], text[1], message.chat.id)

    bot.send_message(message.chat.id, text1)
    bot.send_message(message.chat.id, f"В базе данных {num_words(message.chat.id)} слов.")
    create_cards(message)



"""Обработка текстовых сообщений выбора слов"""
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
            add_log(datetime.datetime.now(), message.chat.id, translate_word(target_word), 'test', True)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
            add_log(datetime.datetime.now(), message.chat.id, translate_word(target_word), 'test', False)
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))

if __name__ == '__main__':
    bot.infinity_polling(skip_pending=True)