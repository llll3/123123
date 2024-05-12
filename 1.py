import telebot
from telebot import types
import re
import time
from functools import wraps
from cachetools import TTLCache

bot = telebot.TeleBot('7018618926:AAEadbtQEiwryYeHCzc3SRsciEtIe0i55U4')
authorized_ids = set()


# Создаем кеш с истечением срока действия через 1 минуту
cache = TTLCache(maxsize=100, ttl=30)

def authorized_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = args[0].from_user.id
        if cache.get(user_id):
            return func(*args, **kwargs)
        else:
            bot.send_message(args[0].chat.id, "<b>Доступ запрещен.</b>", parse_mode="html")
            return

    return wrapper

@bot.message_handler(commands=['start'])
def start(message):
    # Загружаем список администраторов из файла
    with open("Admins.txt", "r") as f:
        authorized_ids = [int(line.strip()) for line in f]

    # Добавляем список администраторов в кеш
    for admin_id in authorized_ids:
        cache[admin_id] = True

    user_id = message.from_user.id
    if not cache.get(user_id):
        bot.send_message(message.chat.id, "<b>Доступ запрещен.</b>", parse_mode="html")
        return

    # Создаем клавиатуру
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_link = telebot.types.KeyboardButton("Ссылка")
    button_stats = telebot.types.KeyboardButton("Статистика")
    button_adminss = telebot.types.KeyboardButton("Администраторы")
    keyboard.add(button_link, button_stats, button_adminss)

    # Отправляем клавиатуру пользователю
    bot.send_message(message.chat.id, "<b>Выберите действие:</b>", reply_markup=keyboard, parse_mode="html")

@bot.message_handler(func=lambda message: message.text == "Администраторы")
@authorized_only

def adminss(message):

    with open("Admins.txt", "r") as f:
        admins = [line.strip() for line in f]

    admins_str = "<b>Список Администраторов:</b>\n\n"
    count = 1
    for admin in admins:
        admins_str += f"<b>[{count}] <a href='tg://user?id={admin}'>{admin}</a>\n</b>"  # Изменена строка для добавления гиперссылки на профиль пользователя
        count += 1

    time.sleep(0.5)  # Добавлена задержка в 500 мс
    bot.send_message(message.chat.id, admins_str, parse_mode="html")

    # Создаем клавиатуру
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_add = telebot.types.KeyboardButton("Добавить")
    button_del = telebot.types.KeyboardButton("Удалить")
    button_back = telebot.types.KeyboardButton("Назад")
    keyboard.add(button_add, button_del, button_back)

    # Отправляем клавиатуру пользователю
    bot.send_message(message.chat.id, "<b>Выберите действие:</b>", reply_markup=keyboard, parse_mode="html")

@bot.message_handler(func=lambda message: message.text == "Добавить")
@authorized_only
def add_admin(message):

    # Очищаем клавиатуру
    keyboard = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "<b>Введите ID нового администратора:</b>", reply_markup=keyboard, parse_mode="html")
    bot.register_next_step_handler(message, add_admin)

@authorized_only
def add_admin(message):
    admin_id = message.text

    # Проверяем, что введенный текст содержит только цифры
    if not re.match("^[0-9]+$", admin_id):
        bot.send_message(message.chat.id, "<b>ID администратора должен содержать только цифры</b>", parse_mode="html")
        return  # Прерываем выполнение функции

    with open("Admins.txt", "a") as f:
        f.write("\n" + admin_id)

    f.close()

    authorized_ids.add(int(admin_id))

    bot.send_message(message.chat.id, "<b>Успешно добавлено!</b>", parse_mode="html")
    adminss(message)


@bot.message_handler(func=lambda message: message.text == "Удалить")
@authorized_only
def del_admin(message):

    # Очищаем клавиатуру
    keyboard = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "<b>Введите порядковый номер администратора для удаления:</b>", reply_markup=keyboard, parse_mode="html")
    bot.register_next_step_handler(message, del_admin)

@authorized_only
def del_admin(message):
    admin_number = message.text

    # Проверяем, что введенный текст содержит только цифры
    if not re.match("^[0-9]+$", admin_number):
        bot.send_message(message.chat.id, "<b>Порядковый номер администратора должен содержать только цифры.</b>", parse_mode="html")
        return  # Прерываем выполнение функции

    admins = []
    with open("Admins.txt", "r") as f:
        admins = [line.strip() for line in f]

    # Преобразуем порядковый номер в индекс
    index = int(admin_number) - 1

    # Проверяем, что введенный порядковый номер корректен
    if index < 0 or index >= len(admins):
        bot.send_message(message.chat.id, "<b>Некорректный порядковый номер администратора</b>", parse_mode="html")
        return

    admin_id = admins[index]

    # Удаляем администратора из списка
    admins.pop(index)
    #if admins:  # Проверка, не пуст ли список
    #    admins[index - 1] += "\n"
    with open("Admins.txt", "w") as f:
        f.write("\n".join(admins))

    bot.send_message(message.chat.id, "<b>Успешно удалено!</b>", parse_mode="html")
    f.close()
    adminss(message)


@bot.message_handler(func=lambda message: message.text == "Назад")
def back(message):
    start(message)

@bot.message_handler(func=lambda message: message.text == "Статистика")
@authorized_only
def stats(message):
    # Считываем данные из файла Users.txt
    with open('Users.txt', 'r') as f:
        lines = f.readlines()

    # Инициализируем счетчики для каждого периода времени
    last_month_users = 0
    current_month_users = 0
    current_week_users = 0
    current_day_users = 0

    # Обрабатываем каждую строку в файле и обновляем счетчики
    for line in lines:
        user_id, timestamp = line.split(' - ')
        timestamp = float(timestamp.split('.')[0])

        # Определяем период времени, к которому относится запись
        if timestamp > time.time() - 60 * 60 * 24:  # меньше дня назад
            current_day_users += 1
        elif timestamp > time.time() - 60 * 60 * 24 * 7:  # меньше недели назад
            current_week_users += 1
        elif timestamp > time.time() - 60 * 60 * 24 * 30:  # меньше месяца назад
            current_month_users += 1
        else:  # больше месяца назад
            last_month_users += 1

    # Создаем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_back = types.KeyboardButton("Назад")
    keyboard.add(button_back)

    msg1 = bot.send_message(message.chat.id, "<b>Статистика:</b>", reply_markup=keyboard, parse_mode="html")

    # Выводим метрики
    bot.send_message(message.chat.id, f"<b>Количество пользователей:\n"
                                      f"\nЗа прошлый месяц: {last_month_users}"
                                      f"\nЗа текущий месяц: {current_month_users}"
                                      f"\nЗа текущую неделю: {current_week_users}"
                                      f"\nЗа текущий день: {current_day_users}</b>", parse_mode="html")

    bot.register_next_step_handler(msg1, back)

@authorized_only
def back(message):
    if message.text == "Назад":
        start(message)
    else:
        bot.send_message(message.chat.id, "<b>Неверный выбор. Повторите попытку.</b>", parse_mode="html")
        link(message)


@bot.message_handler(func=lambda message: message.text == "Ссылка")
@authorized_only
def link(message):
    # Читаем файл Link_edit.txt
    with open('Link_edit.txt', 'r') as f:
        file_content = f.read()

    # Извлекаем старую ссылку
    old_link = file_content.split()[0]

    # Создаем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_new_link = types.KeyboardButton("Изменить ссылку")
    button_back = types.KeyboardButton("Назад")
    keyboard.add(button_new_link, button_back)

    # Отправляем пользователю сообщение со старой ссылкой и клавиатурой
    msg = bot.send_message(message.chat.id, f"<b>Текущая ссылка на папку: {old_link}\n\nВыберите действие:</b>",
                           reply_markup=keyboard, disable_web_page_preview=True, parse_mode="html")
    bot.register_next_step_handler(msg, handle_link_action)

@authorized_only
def handle_link_action(message):
    if message.text == "Изменить ссылку":
        new_link(message, reply_markup=types.ReplyKeyboardRemove())
    elif message.text == "Назад":
        start(message)
    else:
        bot.send_message(message.chat.id, "<b>Неверный выбор. Повторите попытку.</b>", parse_mode="html")
        link(message)

@authorized_only
def new_link(message, reply_markup=None):
    msg = bot.send_message(message.chat.id, "<b>Введите новую ссылку:</b>", parse_mode="html",
                           reply_markup=reply_markup)
    bot.register_next_step_handler(msg, process_new_link)

@authorized_only
def process_new_link(message):
    new_link = message.text

    with open('Link_edit.txt', 'w') as f:
        f.write(new_link)

    bot.send_message(message.chat.id, "<b>Ссылка успешно обновлена!</b>", parse_mode="html")
    start(message)


bot.infinity_polling()
