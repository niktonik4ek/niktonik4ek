import telebot
import random
import os
import time
import datetime
import pytz
from gtts import gTTS

# Ваш API токен
API_TOKEN = "7062301942:AAGQ1yt4RICzqPoIBVzGvQ3N1EP70TjNZlY"
bot = telebot.TeleBot(API_TOKEN)

# Имя файлов для хранения информации о пользователях и билетах
DATA_FILE = 'currency_data.txt'
USERS_FILE = 'users.txt'
TICKETS_FILE = 'tickets_data.txt'

# ID администратора
ADMIN_ID = '6490519873'

# Инициализация переменных для TTS
is_tts_mode = {}
tts_activation_time = {}
selected_language = {}
selected_voice = {}

def load_data():
    """Загружает данные пользователей из файла."""
    data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 4:
                    user_id = parts[0].split(':')[1].strip()
                    username = parts[1].split(':')[1].strip()
                    amount = int(parts[2].split(':')[1].strip())
                    last_claim = float(parts[3].split(':')[1].strip())
                    data[user_id] = {
                        'username': username,
                        'amount': amount,
                        'last_claim': last_claim
                    }
    return data

def save_data(user_id, username, currency_amount, last_claim):
    """Сохраняет данные о пользователе в файл."""
    data = load_data()
    data[user_id] = {
        'username': username,
        'amount': currency_amount,
        'last_claim': last_claim
    }
    with open(DATA_FILE, 'w') as f:
        for uid, user_info in data.items():
            f.write(f'User ID: {uid} | Username: {user_info["username"]} | Amount: {user_info["amount"]} | Last Claim: {user_info["last_claim"]}\n')

def load_tickets():
    """Загружает данные о билетах пользователей из файла."""
    tickets = {}
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) == 2:
                    user_id = parts[0].split(':')[1].strip()
                    tickets_count = int(parts[1].split(':')[1].strip())
                    tickets[user_id] = tickets_count
    return tickets

def save_tickets(user_id, tickets_count):
    """Сохраняет данные о билетах пользователей в файл."""
    tickets = load_tickets()
    tickets[user_id] = tickets_count
    with open(TICKETS_FILE, 'w') as f:
        for uid, count in tickets.items():
            f.write(f'User ID: {uid} | Tickets: {count}\n')

def generate_random_emojis():
    """Генерирует три случайных смайла."""
    emojis = ['😊', '😂', '😍', '🥺', '😎', '😢']
    return [random.choice(emojis) for _ in range(3)]

def check_slots(slots):
    """Проверяет, есть ли три одинаковых смайла в ряд."""
    return slots[0] == slots[1] == slots[2]

def find_user_id_by_username(username):
    """Находит ID пользователя по юзернейму."""
    data = load_data()
    for user_id, user_info in data.items():
        if user_info['username'] == username:
            return user_id
    return None

@bot.message_handler(commands=['get_money'])
def get_currency(message):
    """Обрабатывает команду для получения валюты."""
    user_id = str(message.from_user.id)
    username = message.from_user.username

    # Загрузим данные
    data = load_data()
    current_time = time.time()

    # Проверяем, есть ли пользователь в данных
    if user_id in data:
        last_claim = data[user_id]['last_claim']

        # Проверяем, прошло ли 10 секунд с последнего получения
        if current_time - last_claim < 10:
            remaining_time = 10 - (current_time - last_claim)
            bot.reply_to(message, f'Подождите {int(remaining_time)} секунд(ы) до следующего получения валюты.')
            return
    else:
        last_claim = 0

    # Генерация случайной суммы валюты
    currency_amount = random.randint(1000, 10000)

    # Сохраняем информацию о пользователе в файл
    save_data(user_id, username, currency_amount, current_time)

    bot.reply_to(message, f'Вы получили {currency_amount} игровой валюты!')

@bot.message_handler(commands=['spin'])
def spin(message):
    """Обрабатывает команду для крутилки и выдачи билета при условии наличия достаточного количества валюты."""
    user_id = str(message.from_user.id)
    data = load_data()
    tickets = load_tickets()

    if user_id not in data:
        bot.reply_to(message, 'Сначала получите валюту командой /get_money.')
        return

    user_data = data[user_id]
    if user_data['amount'] < 100000:
        bot.reply_to(message, 'Недостаточно валюты для выполнения команды. Вам нужно 100000 игровой валюты.')
        return

    # Генерация случайных смайлов
    slots = generate_random_emojis()
    if check_slots(slots):
        # Увеличение количества билетов
        user_tickets = tickets.get(user_id, 0) + 1
        save_tickets(user_id, user_tickets)

        # Уменьшение валюты на 100000
        new_amount = user_data['amount'] - 100000
        save_data(user_id, user_data['username'], new_amount, user_data['last_claim'])
        bot.reply_to(message, f'Поздравляю, у вас три одинаковых смайла: {slots}. Вы получили один билетик. У вас теперь {user_tickets} билетиков. Ваш баланс: {new_amount} валюты.')
    else:
        # Уменьшение валюты на 100000
        new_amount = user_data['amount'] - 100000
        save_data(user_id, user_data['username'], new_amount, user_data['last_claim'])
        bot.reply_to(message, f'Не получилось! Выпало: {" | ".join(slots)}. Попробуйте еще раз. Ваш баланс: {new_amount} валюты.')

@bot.message_handler(commands=['balance'])
def balance(message):
    """Отображает баланс пользователя и количество билетов."""
    user_id = str(message.from_user.id)
    data = load_data()
    tickets = load_tickets()

    if user_id not in data:
        bot.reply_to(message, 'Сначала получите валюту командой /get_money.')
        return

    user_data = data[user_id]
    user_tickets = tickets.get(user_id, 0)
    bot.reply_to(message, f'Ваш баланс: {user_data["amount"]} валюты. У вас {user_tickets} билетиков.')

@bot.message_handler(commands=['show_all_users'])
def show_all_users(message):
    """Отображает баланс и количество билетов всех пользователей. Доступно только администратору."""
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return

    data = load_data()
    tickets = load_tickets()

    response = "Баланс и количество билетов всех пользователей:\n\n"
    for user_id, user_info in data.items():
        username = user_info['username']
        amount = user_info['amount']
        user_tickets = tickets.get(user_id, 0)
        response += f"User ID: {user_id} | Username: @{username} | Баланс: {amount} | Билетиков: {user_tickets}\n"

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['showusers'])
def show_users(message):
    """Отображает список пользователей. Доступно только администратору."""
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return

    data = load_data()
    response = "Список пользователей, которые запускали бота:\n\n"
    for user_id, user_info in data.items():
        username = user_info['username']
        response += f"User ID: {user_id} | Username: @{username}\n"

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обрабатывает команду /start и сохраняет информацию о пользователе."""
    username = message.from_user.username
    full_name = message.from_user.full_name
    user_id = str(message.from_user.id)
    tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

    # Проверяем наличие пользователя в данных
    data = load_data()
    if user_id not in data:
        save_data(user_id, username, 0, 0)  # Начинаем с 0 валюты и последнего получения 0

    bot.reply_to(message, f"Привет, {full_name}! Добро пожаловать в Ggamebelbot. С ним ты можешь провести время, или добавить меня в группу, и там мы тоже сможем пообщатся :-)\n \n\nВремя (по мск): {current_time}")

@bot.message_handler(commands=['help'])
def handle_help(message):
    """Отображает справку о командах."""
    help_text = (
        "/get_money - Получить игровую валюту\n"
        "/spin - Крутить барабан на смайлы\n"
        "/balance - Проверить свой баланс и количество билетов\n"
        "/show_all_users - Показать баланс и количество билетов всех пользователей (только администратору)\n"
        "/showusers - Показать список всех пользователей, которые запускали бота (только администратору)\n"
        "/transfer_currency <username> <amount> - Перевести валюту другому пользователю по юзернейму\n"
        "/transfer_tickets <username> <amount> - Перевести билеты другому пользователю по юзернейму\n"
        "/admin_give_currency <user_id> <amount> - Выдать валюту пользователю по ID (только администратору)\n"
        "/admin_give_tickets <user_id> <amount> - Выдать билеты пользователю по ID (только администратору)\n"
        "/help - Вызов данного сообщения\n"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['tts'])
def tts(message):
    """Обрабатывает команду для использования TTS."""
    user_id = str(message.from_user.id)
    tickets = load_tickets()

    if user_id not in tickets or tickets[user_id] < 5:
        bot.reply_to(message, 'Для использования TTS необходимо иметь 5 билетов.')
        return

    current_time = time.time()
    if user_id in tts_activation_time:
        activation_time = tts_activation_time[user_id]
        if current_time - activation_time < 600:  # 10 минут = 600 секунд
            bot.reply_to(message, 'Вы уже активировали режим TTS. Пожалуйста, подождите 10 минут, прежде чем активировать его снова.')
            return
        else:
            # Время активации устарело, сбрасываем таймер
            tts_activation_time[user_id] = current_time
    else:
        tts_activation_time[user_id] = current_time

    # Списание билетов
    tickets[user_id] -= 5
    save_tickets(user_id, tickets[user_id])
    bot.reply_to(message, 'Режим TTS активирован на 10 минут.')

@bot.message_handler(commands=['tts_on'])
def tts_on(message):
    """Включает режим TTS для пользователя."""
    user_id = str(message.from_user.id)
    if user_id in tts_activation_time and (time.time() - tts_activation_time[user_id]) < 600:
        is_tts_mode[user_id] = True
        bot.reply_to(message, "Режим TTS включен.")
    else:
        bot.reply_to(message, 'Сначала активируйте режим TTS командой /tts.')

@bot.message_handler(commands=['tts_off'])
def tts_off(message):
    """Выключает режим TTS для пользователя."""
    user_id = str(message.from_user.id)
    is_tts_mode[user_id] = False
    bot.reply_to(message, "Режим TTS выключен.")

@bot.message_handler(commands=['set_lang'])
def set_language(message):
    """Устанавливает язык TTS для пользователя."""
    user_id = str(message.from_user.id)
    lang = message.text.split(' ', 1)[1].strip()  # Получаем язык из команды
    selected_language[user_id] = lang
    bot.reply_to(message, f"Язык TTS установлен на {lang}.")

@bot.message_handler(commands=['set_voice'])
def set_voice(message):
    """Устанавливает голос TTS для пользователя."""
    user_id = str(message.from_user.id)
    voice = message.text.split(' ', 1)[1].strip()  # Получаем голос из команды
    selected_voice[user_id] = voice
    bot.reply_to(message, f"Голос TTS установлен на {voice}.")

@bot.message_handler(commands=['transfer_currency'])
def transfer_currency(message):
    """Обрабатывает команду для перевода валюты между пользователями по юзернейму."""
    user_id = str(message.from_user.id)
    parts = message.text.split()

    if len(parts) != 3:
        bot.reply_to(message, 'Неверный формат команды. Используйте: /transfer_currency <username> <amount>')
        return

    target_username = parts[1]
    amount = int(parts[2])

    data = load_data()

    if user_id not in data:
        bot.reply_to(message, 'Вы не зарегистрированы в системе. Сначала получите валюту командой /get_money.')
        return

    target_user_id = find_user_id_by_username(target_username)
    if not target_user_id:
        bot.reply_to(message, 'Целевой пользователь не найден.')
        return

    if data[user_id]['amount'] < amount:
        bot.reply_to(message, 'Недостаточно валюты для перевода.')
        return

    # Выполняем перевод
    data[user_id]['amount'] -= amount
    data[target_user_id]['amount'] += amount
    save_data(user_id, data[user_id]['username'], data[user_id]['amount'], data[user_id]['last_claim'])
    save_data(target_user_id, data[target_user_id]['username'], data[target_user_id]['amount'], data[target_user_id]['last_claim'])

    # Уведомляем целевого пользователя
    bot.send_message(target_user_id, f'Вам было переведено {amount} валюты от пользователя @{data[user_id]["username"]}.')

    bot.reply_to(message, f'Вы перевели {amount} валюты пользователю @{target_username}.')

@bot.message_handler(commands=['admin_give_tickets'])
def admin_give_tickets(message):
    """Обрабатывает команду для выдачи билетов пользователю по ID (только администратору)."""
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return

    parts = message.text.split()

    if len(parts) != 3:
        bot.reply_to(message, 'Неверный формат команды. Используйте: /admin_give_tickets <user_id> <amount>')
        return

    target_user_id = parts[1]
    amount = int(parts[2])

    tickets = load_tickets()

    if target_user_id not in tickets:
        bot.reply_to(message, 'Целевой пользователь не найден.')
        return

    # Выполняем выдачу билетов
    tickets[target_user_id] += amount
    save_tickets(target_user_id, tickets[target_user_id])

    # Уведомляем целевого пользователя
    data = load_data()
    target_username = data[target_user_id]['username']
    bot.send_message(target_user_id, f'Вам было выдано {amount} билетов от администрации.')

    bot.reply_to(message, f'Вы выдали {amount} билетов пользователю с ID {target_user_id}.')

@bot.message_handler(commands=['admin_give_currency'])
def admin_give_currency(message):
    """Обрабатывает команду для выдачи валюты пользователю по ID (только администратору)."""
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return

    parts = message.text.split()

    if len(parts) != 3:
        bot.reply_to(message, 'Неверный формат команды. Используйте: /admin_give_currency <user_id> <amount>')
        return

    target_user_id = parts[1]
    amount = int(parts[2])

    data = load_data()

    if target_user_id not in data:
        bot.reply_to(message, 'Целевой пользователь не найден.')
        return

    # Выполняем выдачу валюты
    data[target_user_id]['amount'] += amount
    save_data(target_user_id, data[target_user_id]['username'], data[target_user_id]['amount'], data[target_user_id]['last_claim'])

    # Уведомляем целевого пользователя
    target_username = data[target_user_id]['username']
    bot.send_message(target_user_id, f'Вам было выдано {amount} валюты от администрации.')

    bot.reply_to(message, f'Вы выдали {amount} валюты пользователю с ID {target_user_id}.')

@bot.message_handler(commands=['exchange'])
def exchange_ticket(message):
    user_id = str(message.from_user.id)

    try:
        # Получаем количество тикетов из сообщения
        ticket_amount = int(message.text.split()[1])
    except (IndexError, ValueError):
        bot.reply_to(message, 'Пожалуйста, укажите количество тикетов для обмена. Например: /exchange 3')
        return

    tickets = load_tickets()
    data = load_data()

    if user_id not in tickets:
        bot.reply_to(message, "Вы не зарегистрированы в системе.")
        return

    if tickets[user_id] < ticket_amount:
        bot.reply_to(message, "У вас недостаточно тикетов для обмена.")
        return

    # Обмен тикетов на валюту
    currency_amount = ticket_amount * 10000000  # 10 миллионов за тикет
    tickets[user_id] -= ticket_amount

    if user_id in data:
        data[user_id]['amount'] += currency_amount
        save_data(user_id, data[user_id]['username'], data[user_id]['amount'], data[user_id]['last_claim'])
        save_tickets(user_id, tickets[user_id])
        bot.reply_to(message, f"Вы обменяли {ticket_amount} тикетов на {currency_amount} игровой валюты.")
    else:
        bot.reply_to(message, "Ошибка при обмене тикетов.")


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обрабатывает текстовые сообщения и отправляет их с TTS."""
    user_id = str(message.from_user.id)

    # Проверяем, включен ли TTS и активирован ли режим
    if is_tts_mode.get(user_id, False) and user_id in tts_activation_time and (time.time() - tts_activation_time[user_id]) < 600:
        lang = selected_language.get(user_id, 'ru')
        voice = selected_voice.get(user_id, 'female')  # Пример использования голоса (пока не реализовано)

        tts = gTTS(text=message.text, lang=lang)
        tts_file = f'{user_id}_message.mp3'
        tts.save(tts_file)

        with open(tts_file, 'rb') as audio_file:
            bot.send_audio(message.chat.id, audio_file)

        os.remove(tts_file)

bot.polling(none_stop=True)
