# discord-voice-bot
# Discord Voice Bot

## Установка на сервер

1. Клонировать репозиторий:
```bash
cd ~
git clone https://github.com/ваш_username/discord-voice-bot.git botsds
cd botsds
```

2. Создать виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Настроить systemd сервис:
```bash
nano /etc/systemd/system/discord-bot.service
# Вставить содержимое из discord-bot.service
systemctl daemon-reload
systemctl enable discord-bot
systemctl start discord-bot
```
```

5. Добавьте файл с настройками службы:
```ini:discord-bot.service
[Unit]
Description=Discord Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/botsds
ExecStart=/root/botsds/venv/bin/python3 /root/botsds/bot.py
Environment=PYTHONPATH=/root/botsds/venv/lib/python3.8/site-packages
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

6. Теперь при проблемах с сервером:
```bash
# На новом сервере
cd ~
git clone https://github.com/ваш_username/discord-voice-bot.git botsds
cd botsds
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка службы
sudo cp discord-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

7. Для обновления бота:
```bash
# Локально после изменений
git add .
git commit -m "Описание изменений"
git push

# На сервере
cd ~/botsds
git pull
systemctl restart discord-bot
```

Преимущества:
- Резервное копирование кода
- История изменений
- Быстрое восстановление на новом сервере
- Удобное управление обновлениями
- Документация всегда под рукой

Безопасность:
1. Храните токен бота отдельно в файле config.json или .env
2. Не публикуйте токен в GitHub
3. Используйте приватный репозиторий

Дополнительно можно настроить:
- GitHub Actions для автоматического деплоя
- Ветки для тестирования новых функций
- Issues для отслеживания задач и багов
