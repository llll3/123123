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

function_number = 0

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
            msg = bot.send_message(args[0].chat.id, "<b>Доступ запрещен.</b>\U0000274C", parse_mode="html")
            bot.delete_message(args[0].chat.id, args[0].message_id)
            threading.Timer(2.0, bot.delete_message, (msg.chat.id, msg.message_id)).start()
            time.sleep(2.0)
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
    global mm
    # Получение количества отправленных сообщений пользователем
    message_count = get_user_message_count(message.chat.id)

    # Вывод количества отправленных сообщений в консоль
    print(f"Пользователь {message.from_user.first_name} отправил {message_count} сообщений.")

    # Увеличение счетчика сообщений пользователя
    update_user_message_count(message.chat.id, message_count + 1)
    admins = set()
    with open("Admins.txt", "r") as f:
        admins = {int(line.strip()) for line in f}
    for admin_id in admins:
        cache[admin_id] = True
    user_id = message.from_user.id
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    if not cache.get(user_id):
        msg2 = bot.send_message(message.chat.id, "<b>Доступ запрещен</b>\U0000274C", parse_mode="html")
        update_user_message_count(message.chat.id, message_count = "0")
        time.sleep(2.0)
        try:
            bot.delete_message(mm.chat.id, mm.message_id)
        except Exception:
            pass
        threading.Timer(2.0, bot.delete_message, (msg2.chat.id, msg2.message_id)).start()
        return
        # Приветственное сообщение
    if message_count == 0:
        bot.send_message(message.chat.id, f"<b>Добро пожаловать, <a href='tg://user?id={message.from_user.id}'>\
{message.from_user.first_name}</a>!</b>", parse_mode="html")
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [types.KeyboardButton(btn) for btn in ["Ссылка", "Статистика", "Администраторы"]]
    keyboard.add(*buttons)
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    mm = bot.send_message(message.chat.id, "<b>Выберите действие</b>", reply_markup=keyboard, parse_mode="html",
                          disable_notification=True)

@bot.message_handler(func=lambda message: message.text == "Ссылка")
@authorized_only
def link(message):
    global msg_link
    with open('Link_edit.txt', 'r') as f:
        file_content = f.read()
    old_link = file_content.split()[0]
    try:
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(mm.chat.id, mm.message_id)
    except Exception:
        pass
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_new_link = types.KeyboardButton("Изменить ссылку")
    button_back = types.KeyboardButton("Назад")
    keyboard.add(button_new_link, button_back)
    msg_link = bot.send_message(message.chat.id, f"<b>Текущая ссылка на папку: {old_link}</b>",
                           reply_markup=keyboard, disable_web_page_preview=True, parse_mode="html")
    bot.register_next_step_handler(msg_link, handle_link_action)

def handle_link_action(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    if message.text == "Изменить ссылку":
        bot.delete_message(message.chat.id, msg_link.message_id)
        new_link(message, reply_markup=types.ReplyKeyboardRemove())
    elif message.text == "Назад":
        bot.delete_message(message.chat.id, msg_link.message_id)
        start(message)
    else:
        msg_error = bot.send_message(message.chat.id, "<b>Неверный выбор. Повторите попытку.</b>\U0000274C", parse_mode="html")
        bot.delete_message(message.chat.id, msg_link.message_id)
        threading.Timer(2.0, bot.delete_message, (msg_error.chat.id, msg_error.message_id)).start()
        time.sleep(2.0)
        link(message)

def new_link(message, reply_markup=None):
    global msg_new_link
    msg_new_link = bot.send_message(message.chat.id, "<b>Введите новую ссылку:</b>", parse_mode="html",
                           reply_markup=reply_markup)
    bot.register_next_step_handler(msg_new_link, process_new_link)

def process_new_link(message):
    try:
        bot.delete_message(msg_new_link.chat.id, msg_new_link.message_id)
    except Exception:
        pass
    new_link = message.text
    with open('Link_edit.txt', 'w') as f:
        f.write(new_link)
    msg_link_add = bot.send_message(message.chat.id, "<b>Ссылка успешно обновлена!</b>\U00002705", parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_link_add.chat.id, msg_link_add.message_id)).start()
    time.sleep(2.0)
    link(message)

@bot.message_handler(func=lambda message: message.text == "Администраторы")
@authorized_only
def adminss(message):
    global msg_admm
    try:
        bot.delete_message(mm.chat.id, mm.message_id)
    except Exception:
        pass
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
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    bot.register_next_step_handler(msg_admm, handle_admm_action)
def handle_admm_action(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    if message.text == "Добавить":
        bot.delete_message(message.chat.id, msg_admm.message_id)
        add_admin(message)
    elif message.text == "Удалить":
        del_admin(message)
    elif message.text == "Назад":
        bot.delete_message(message.chat.id, msg_admm.message_id)
        start(message)
    else:
        msg_error = bot.send_message(message.chat.id, "<b>Неверный выбор. Повторите попытку.</b>\U0000274C", parse_mode="html")
        bot.delete_message(message.chat.id, msg_admm.message_id)
        threading.Timer(2.0, bot.delete_message, (msg_error.chat.id, msg_error.message_id)).start()
        time.sleep(2.0)
        adminss(message)
def add_admin(message):
    global msg_adm4
    keyboard = types.ReplyKeyboardRemove()
    msg_adm4 = bot.send_message(message.chat.id, "<b>Введите ID нового администратора:</b>", reply_markup=keyboard, parse_mode="html")
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    bot.register_next_step_handler(msg_adm4, add_admin1)

def add_admin1(message):
    try:
        bot.delete_message(msg_adm4.chat.id, msg_adm4.message_id)
    except Exception:
        pass
    admin_id = message.text
    if not re.match("^[0-9]+$", admin_id):
        msg_adm6 = bot.send_message(message.chat.id, "<b>ID администратора должен содержать только цифры!</b>\U0000274C", parse_mode="html")
        threading.Timer(3.0, bot.delete_message, (msg_adm6.chat.id, msg_adm6.message_id)).start()
        time.sleep(3.0)
        add_admin(message)
        return
    with open("Admins.txt", "a") as f:
        f.write("\n" + admin_id)
    f.close()
    authorized_ids.add(int(admin_id))
    msg_adm5 = bot.send_message(message.chat.id, "<b>Успешно добавлено!</b>\U00002705", parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_adm5.chat.id, msg_adm5.message_id)).start()
    time.sleep(2.0)
    adminss(message)

def del_admin(message):
    global msg_adm3
    keyboard = types.ReplyKeyboardRemove()
    msg_adm3 = bot.send_message(message.chat.id, "<b>Введите порядковый номер администратора для удаления:</b>", reply_markup=keyboard, parse_mode="html")
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    bot.register_next_step_handler(msg_adm3, del_admin1)

def del_admin1(message):
    try:
        bot.delete_message(msg_adm3.chat.id, msg_adm3.message_id)
    except Exception:
        pass
    admin_number = message.text
    if not re.match("^[0-9]+$", admin_number):
        msg_adm2 = bot.send_message(message.chat.id, "<b>Порядковый номер администратора должен содержать только цифры.</b>\U0000274C", parse_mode="html")
        threading.Timer(3.0, bot.delete_message, (msg_adm2.chat.id, msg_adm2.message_id)).start()
        time.sleep(3.0)
        del_admin(message)
        return
    admins = []
    with open("Admins.txt", "r") as f:
        admins = [line.strip() for line in f]
    index = int(admin_number) - 1
    if index < 0 or index >= len(admins):
        msg_adm1 = bot.send_message(message.chat.id, "<b>Некорректный порядковый номер администратора</b>\U0000274C", parse_mode="html")
        threading.Timer(3.0, bot.delete_message, (msg_adm1.chat.id, msg_adm1.message_id)).start()
        time.sleep(3.0)
        del_admin(message)
        return
    admin_id = admins[index]
    admins.pop(index)
    with open("Admins.txt", "w") as f:
        f.write("\n".join(admins))
    try:
        bot.delete_message(message.chat.id, msg_admm.message_id)
    except Exception:
        pass
    msg_del = bot.send_message(message.chat.id, "<b>Успешно удалено!\U00002705</b>", parse_mode="html")
    threading.Timer(2.0, bot.delete_message, (msg_del.chat.id, msg_del.message_id)).start()
    time.sleep(2.0)
    f.close()
    adminss(message)


@bot.message_handler(func=lambda message: message.text == "Статистика")
@authorized_only
def stats(message):
    global msg_stats1
    try:
        bot.delete_message(mm.chat.id, mm.message_id)
    except Exception:
        pass
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
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    msg_stats1 = bot.send_message(message.chat.id, f"<b>Количество пользователей:\n"
                                      f"\nЗа прошлый месяц: {stats['last_month']}"
                                      f"\nЗа текущий месяц: {stats['current_month']}"
                                      f"\nЗа текущую неделю: {stats['current_week']}"
                                      f"\nЗа текущий день: {stats['current_day']}</b>",
                                  reply_markup=keyboard, parse_mode="html")
    bot.register_next_step_handler(msg_stats1, handle_stats_action)

def handle_stats_action(message):
    bot.delete_message(message.chat.id, message.message_id)
    if message.text == "Назад":
        bot.delete_message(message.chat.id, msg_stats1.message_id)
        start(message)
    elif message.text == "Назадlll":
        pass
    else:
        msg_error = bot.send_message(message.chat.id, "<b>Неверный выбор. Повторите попытку.</b>\U0000274C", parse_mode="html")
        bot.delete_message(message.chat.id, msg_stats1.message_id)
        threading.Timer(2.0, bot.delete_message, (msg_error.chat.id, msg_error.message_id)).start()
        time.sleep(2.0)
        stats(message)

bot.infinity_polling()
