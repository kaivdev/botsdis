import discord
from discord.ext import commands, tasks
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Настройка бота с полными интентами
intents = discord.Intents.all()  # Включаем все интенты

bot = commands.Bot(command_prefix='!', intents=intents)

# Словари для отслеживания
last_join = {}
last_leave = {}
user_voice_time = defaultdict(int)  # Общее время в голосовых каналах
user_session_start = {}  # Время начала текущей сессии
COOLDOWN_TIME = 300

# Функции для сохранения и загрузки статистики
def save_stats():
    """Сохраняет статистику в файл"""
    data = {
        'user_voice_time': dict(user_voice_time),
        'last_reset': time.time()
    }
    with open('voice_stats.json', 'w') as f:
        json.dump(data, f)

def load_stats():
    """Загружает статистику из файла"""
    try:
        with open('voice_stats.json', 'r') as f:
            data = json.load(f)
            # Преобразуем ключи обратно в int, так как JSON хранит их как строки
            user_voice_time.clear()
            user_voice_time.update({int(k): v for k, v in data['user_voice_time'].items()})
    except FileNotFoundError:
        print("Файл со статистикой не найден, начинаем с пустой статистики")
    except Exception as e:
        print(f"Ошибка при загрузке статистики: {e}")

def format_time(seconds):
    """Форматирует время в читаемый вид"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        if minutes > 0:
            return f"{hours} ч {minutes} мин"
        return f"{hours} ч"
    return f"{minutes} мин"

@bot.event
async def on_ready():
    print(f'{bot.user} подключился к Discord!')
    load_stats()  # Загружаем статистику при запуске
    weekly_report.start()  # Запускаем еженедельный отчет

@bot.event
async def on_voice_state_update(member, before, after):
    try:
        current_time = time.time()
        notification_channel = bot.get_channel(1351697916405874719)
        
        print(f"Обнаружено изменение голосового состояния:")
        print(f"Пользователь: {member.name}")
        print(f"До: {before.channel.name if before.channel else 'Нет канала'}")
        print(f"После: {after.channel.name if after.channel else 'Нет канала'}")
        
        if not notification_channel:
            print(f"Ошибка: Не могу найти канал с ID 1351697916405874719")
            return
            
        try:
            # Вход в канал
            if before.channel is None and after.channel is not None:
                can_send_join = True
                if member.id in last_join:
                    time_passed = current_time - last_join[member.id]
                    print(f"Прошло времени с последнего входа: {time_passed} секунд")
                    if time_passed < COOLDOWN_TIME:
                        can_send_join = False
                        print(f"Сообщение о входе пропущено из-за задержки")
                
                if can_send_join:
                    await notification_channel.send(f'🎤 {member.name} присоединился к голосовому каналу {after.channel.name}')
                    print(f"Отправлено сообщение о входе в канал")
                    last_join[member.id] = current_time
            
            # Выход из канала
            elif before.channel is not None and after.channel is None:
                can_send_leave = True
                if member.id in last_leave:
                    time_passed = current_time - last_leave[member.id]
                    print(f"Прошло времени с последнего выхода: {time_passed} секунд")
                    if time_passed < COOLDOWN_TIME:
                        can_send_leave = False
                        print(f"Сообщение о выходе пропущено из-за задержки")
                
                if can_send_leave:
                    await notification_channel.send(f'👋 {member.name} покинул голосовой канал {before.channel.name}')
                    print(f"Отправлено сообщение о выходе из канала")
                    last_leave[member.id] = current_time
            
            # Переход между каналами
            elif before.channel != after.channel:
                await notification_channel.send(f'↔️ {member.name} перешел из канала {before.channel.name} в канал {after.channel.name}')
                print(f"Отправлено сообщение о переходе между каналами")
                
            # Записываем время начала сессии
            if before.channel is None and after.channel is not None:
                user_session_start[member.id] = current_time
            
            # Подсчитываем время в канале
            if before.channel is not None and after.channel is None:
                if member.id in user_session_start:
                    session_duration = current_time - user_session_start[member.id]
                    user_voice_time[member.id] += session_duration
                    del user_session_start[member.id]
                    save_stats()  # Сохраняем статистику после обновления
                
        except discord.errors.Forbidden:
            print(f"Ошибка: У бота нет прав для отправки сообщений в канал")
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {str(e)}")
                
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

@tasks.loop(hours=168)  # 168 часов = 1 неделя
async def weekly_report():
    notification_channel = bot.get_channel(1351697916405874719)
    
    # Создаем список пользователей и их времени
    user_times = []
    for user_id, total_time in user_voice_time.items():
        try:
            user = await bot.fetch_user(user_id)
            user_times.append((user.name, total_time))
        except:
            continue
    
    # Сортируем по времени и берем топ 5
    top_users = sorted(user_times, key=lambda x: x[1], reverse=True)[:5]
    
    # Формируем отчет
    report = "📊 **Еженедельный отчет по активности в голосовых каналах:**\n\n"
    for i, (name, seconds) in enumerate(top_users, 1):
        formatted_time = format_time(seconds)
        report += f"{i}. {name}: {formatted_time}\n"
    
    await notification_channel.send(report)
    
    # Очищаем статистику и сохраняем пустой файл
    user_voice_time.clear()
    save_stats()

# Команда для получения текущей статистики
@bot.command()
async def stats(ctx):
    # Обновляем время для пользователей, которые сейчас в каналах
    current_time = time.time()
    for user_id in user_session_start:
        session_duration = current_time - user_session_start[user_id]
        user_voice_time[user_id] += session_duration
    
    # Создаем список пользователей и их времени
    user_times = []
    for user_id, total_time in user_voice_time.items():
        try:
            user = await bot.fetch_user(user_id)
            user_times.append((user.name, total_time))
        except:
            continue
    
    # Сортируем по времени и берем топ 5
    top_users = sorted(user_times, key=lambda x: x[1], reverse=True)[:5]
    
    # Формируем отчет
    report = "📊 **Текущая статистика активности в голосовых каналах:**\n\n"
    for i, (name, seconds) in enumerate(top_users, 1):
        formatted_time = format_time(seconds)
        report += f"{i}. {name}: {formatted_time}\n"
    
    await ctx.send(report)
    save_stats()  # Сохраняем обновленную статистику

# Замените 'YOUR_TOKEN' на токен вашего бота
bot.run('MTM1MTYxMzY0NjY3Mjc1Njg2Nw.GyoeUw.2XM-7BieJL-Q8212IXyFq1pcSHv5Srmdazw7Jk') 