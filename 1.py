import telebot
from telebot import types
import time
import re
import threading
from functools import wraps
from cachetools import TTLCache

bot = telebot.TeleBot('7018618926:AAEadbtQEiwryYeHCzc3SRsciEtIe0i55U4')
authorized_ids = set()
cache = TTLCache(maxsize=100, ttl=60)

def edit_message(chat_id, message_id, new_text):
    bot.edit_message_text(new_text, chat_id, message_id, parse_mode="html")

def replace_message(chat_id, message_id, new_text):
    bot.delete_message(chat_id, message_id)
    edit_message(chat_id, message_id, new_text)

def authorized_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = args[0].from_user.id
        if cache.get(user_id):
            return func(*args, **kwargs)
        else:
            msg = bot.send_message(args[0].chat.id, "<b>Доступ запрещен.</b>", parse_mode="html")
            bot.delete_message(args[0].chat.id, args[0].message_id)
            threading.Timer(2.0, bot.delete_message, (msg.chat.id, msg.message_id)).start()
            return
    return wrapper

file_name = 'user_messages_count.txt'


def get_user_message_count(chat_id):
    with open(file_name, 'r') as f:
        data = f.readlines()

    for line in data:
        if str(chat_id) in line:
            return int(line.split(':')[1])
    return 0


def update_user_message_count(chat_id, message_count):
    with open(file_name, 'r') as f:
        data = f.readlines()

    with open(file_name, 'w') as f:
        updated = False
        for line in data:
            if str(chat_id) in line:
                f.write(f"{chat_id}:{message_count}\n")
                updated = True
            else:
                f.write(line)

        if not updated:
            f.write(f"{chat_id}:{message_count}\n")



@bot.message_handler(commands=['start'])
def start(message):
    # Получение количества отправленных сообщений пользователем
    message_count = get_user_message_count(message.chat.id)

    # Вывод количества отправленных сообщений в консоль
    print(f"Пользователь {message.from_user.first_name} отправил {message_count} сообщений.")

    # Увеличение счетчика сообщений пользователя
    update_user_message_count(message.chat.id, message_count + 1)

    # Приветственное сообщение
    if message_count == 0:
        bot.send_message(message.chat.id, f"<b>Добро пожаловать, <a href='tg://user?id={message.from_user.id}'>\
{message.from_user.first_name}</a>!</b>", parse_mode="html")
    admins = set()
    bot.delete_message(message.chat.id, message.message_id)  # Удаление сообщения
    with open("Admins.txt", "r") as f:
        admins = {int(line.strip()) for line in f}
    for admin_id in admins:
        cache[admin_id] = True
    user_id = message.from_user.id
    if not cache.get(user_id):
        msg2 = bot.send_message(message.chat.id, "<b>Доступ запрещен.</b>", parse_mode="html")
        threading.Timer(2.0, bot.delete_message, (msg2.chat.id, msg2.message_id)).start()
        return
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [types.KeyboardButton(btn) for btn in ["Ссылка", "Статистика", "Администраторы"]]
    keyboard.add(*buttons)

    mm = bot.send_message(message.chat.id, "<b>Выберите действие:</b>", reply_markup=keyboard, parse_mode="html",
                          disable_notification=True)

    time.sleep(2.0)
    bot.delete_message(mm.chat.id, mm.message_id)

@bot.message_handler(func=lambda message: message.text == "Ссылка")
@authorized_only
def link(message):
    global msg_link
    link_edit = open('Link_edit.txt', 'r').read()
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [types.KeyboardButton(btn) for btn in ["Изменить ссылку", "Назад"]]
    keyboard.add(*buttons)
    bot.delete_message(message.chat.id, message.message_id)
    # Удаляем HTML-разметку из текста сообщения
    link_edit_without_html = link_edit.replace("<b>", "").replace("</b>", "")
    msg_link = bot.send_message(message.chat.id, f"Текущая ссылка: {link_edit_without_html}", reply_markup=keyboard)
    #bot.register_next_step_handler(msg_link, back_link, handle_link_action)

@bot.message_handler(func=lambda message: message.text == "Изменить ссылку")
@authorized_only
def handle_link_action(message):
    if message.text == "Изменить ссылку":
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, msg_link.message_id)  # Удаляем сообщение со ссылкой
        msg_link2 = bot.send_message(message.chat.id, "<b>Введите новую ссылку:</b>", parse_mode="html", reply_markup=types.ReplyKeyboardRemove())
        threading.Timer(2.0, bot.delete_message, (msg_link2.chat.id, msg_link2.message_id)).start()
        bot.register_next_step_handler(msg_link2, process_new_link)

@bot.message_handler(func=lambda message: message.text == "Администраторы")
@authorized_only
def adminss(message):
    global msg_admm
    with open("Admins.txt", "r") as f:
        admins = [line.strip() for line in f]
    admins_str = "<b>Список Администраторов:</b>\n\n"
    count = 1
    for admin in admins:
        admins_str += f"<b>[{count}] <a href='tg://user?id={admin}'>{admin}</a>\n</b>"
        count += 1
    time.sleep(0.5)  # Добавлена задержка в 500 мс
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [types.KeyboardButton(btn) for btn in ["Добавить", "Удалить", "Назад"]]
    keyboard.add(*buttons)
    msg_admm = bot.send_message(message.chat.id, admins_str, reply_markup=keyboard, parse_mode="html")
    bot.delete_message(message.chat.id, message.message_id)
    #bot.register_next_step_handler(msg_admm, back_admm)

@bot.message_handler(func=lambda message: message.text == "Добавить")
@authorized_only
def add_admin(message):
    bot.delete_message(message.chat.id, msg_admm.message_id)
    keyboard = types.ReplyKeyboardRemove()
    msg_adm4 = bot.send_message(message.chat.id, "<b>Введите ID нового администратора:</b>", reply_markup=keyboard, parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_adm4.chat.id, msg_adm4.message_id)).start()
    bot.register_next_step_handler(message, add_admin)
    bot.delete_message(message.chat.id, message.message_id)

@authorized_only
def add_admin(message):
    admin_id = message.text
    if not re.match("^[0-9]+$", admin_id):
        msg_adm6 = bot.send_message(message.chat.id, "<b>ID администратора должен содержать только цифры</b>", parse_mode="html")
        threading.Timer(2.0, bot.delete_message, (msg_adm6.chat.id, msg_adm6.message_id)).start()
        return
    with open("Admins.txt", "a") as f:
        f.write("\n" + admin_id)
    f.close()
    authorized_ids.add(int(admin_id))
    msg_adm5 = bot.send_message(message.chat.id, "<b>Успешно добавлено!</b>", parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_adm5.chat.id, msg_adm5.message_id)).start()
    adminss(message)

@bot.message_handler(func=lambda message: message.text == "Удалить")
@authorized_only
def del_admin(message):
    keyboard = types.ReplyKeyboardRemove()
    msg_adm3 = bot.send_message(message.chat.id, "<b>Введите порядковый номер администратора для удаления:</b>", reply_markup=keyboard, parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_adm3.chat.id, msg_adm3.message_id)).start()
    bot.register_next_step_handler(message, del_admin)
    bot.delete_message(message.chat.id, message.message_id)

@authorized_only
def del_admin(message):
    admin_number = message.text
    if not re.match("^[0-9]+$", admin_number):
        msg_adm2 = bot.send_message(message.chat.id, "<b>Порядковый номер администратора должен содержать только цифры.</b>", parse_mode="html")
        threading.Timer(2.0, bot.delete_message, (msg_adm2.chat.id, msg_adm2.message_id)).start()
        return
    admins = []
    with open("Admins.txt", "r") as f:
        admins = [line.strip() for line in f]
    index = int(admin_number) - 1
    if index < 0 or index >= len(admins):
        msg_adm1 = bot.send_message(message.chat.id, "<b>Некорректный порядковый номер администратора</b>", parse_mode="html")
        threading.Timer(2.0, bot.delete_message, (msg_adm1.chat.id, msg_adm1.message_id)).start()
        return
    admin_id = admins[index]
    admins.pop(index)
    with open("Admins.txt", "w") as f:
        f.write("\n".join(admins))
    bot.send_message(message.chat.id, "<b>Успешно удалено!</b>", parse_mode="html")
    bot.delete_message(message.chat.id, msg_admm.message_id)
    f.close()
    adminss(message)

@bot.message_handler(func=lambda message: message.text == "Назад")
def back_admm(message):
    bot.delete_message(message.chat.id, msg_admm.message_id)
    start(message)

def back_link(message):
        bot.delete_message(message.chat.id, msg_link.message_id)
        start(message)
def back_stats(message):
        bot.delete_message(message.chat.id, msg_stats1.message_id)
        start(message)

@bot.message_handler(func=lambda message: message.text == "Статистика")
@authorized_only
def stats(message):
    global msg_stats1
    with open('Users.txt', 'r') as f:
        lines = f.readlines()
    stats = {"last_month": 0, "current_month": 0, "current_week": 0, "current_day": 0}
    for line in lines:
        user_id, timestamp = line.split(' - ')
        timestamp = float(timestamp.split('.')[0])
        if timestamp > time.time() - 60 * 60 * 24:
            stats["current_day"] += 1
        elif timestamp > time.time() - 60 * 60 * 24 * 7:
            stats["current_week"] += 1
        elif timestamp > time.time() - 60 * 60 * 24 * 30:
            stats["current_month"] += 1
        else:
            stats["last_month"] += 1
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_back = types.KeyboardButton("Назад")
    keyboard.add(button_back)
    bot.delete_message(message.chat.id, message.message_id)
    msg_stats1 = bot.send_message(message.chat.id, f"<b>Количество пользователей:\n"
                                      f"\nЗа прошлый месяц: {stats['last_month']}"
                                      f"\nЗа текущий месяц: {stats['current_month']}"
                                      f"\nЗа текущую неделю: {stats['current_week']}"
                                      f"\nЗа текущий день: {stats['current_day']}</b>", reply_markup=keyboard, parse_mode="html")
    bot.register_next_step_handler(msg_stats1, back_stats)

@authorized_only
def process_new_link(message):
    new_link = message.text
    with open('Link_edit.txt', 'w') as f:
        f.write(new_link)
    msg_link3 = bot.send_message(message.chat.id, "<b>Ссылка успешно обновлена!</b>", parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_link3.chat.id, msg_link3.message_id)).start()
    start(message)

bot.infinity_polling()
