# Развёртывание бота на Ubuntu (systemd)

Путь к проекту на сервере: **`/opt/davaj_igrat/app`**.

## 0. Запуск локально

- **Windows (PowerShell или Git Bash):** из корня проекта выполните `py main.py` или запустите `run_bot.bat`. Перед первым запуском скопируйте `.env.example` в `.env` и укажите свой `BOT_TOKEN`.
- **Linux:** из каталога проекта выполните `./run_bot.sh` или `python3 main.py`. Аналогично задайте `BOT_TOKEN` в окружении или в `.env`.
- **Проверка без запуска бота:** из корня проекта выполните `python scripts/test_run.py` (проверка импортов и опционально API).

## 1. Команда запуска бота

- **Без venv:** `python3 main.py` из каталога проекта.
- **С venv (рекомендуется):** скрипт `run_bot.sh` сам подхватит `venv` в каталоге проекта и запустит `python3 main.py`.

Создание виртуального окружения на сервере (один раз):

```bash
cd /opt/davaj_igrat/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

После этого `run_bot.sh` будет использовать этот `venv`.

**Токен бота:** задайте переменную окружения `BOT_TOKEN` или создайте файл `.env` в каталоге проекта со строкой `BOT_TOKEN=ваш_токен`. Шаблон — в `.env.example`.

## 2. Установка и запуск сервиса

Подставьте вместо `YOUR_USER` имя пользователя Linux (владелец файлов в `/opt/davaj_igrat/app`), например `ubuntu` или ваш логин.

### 2.1. Подготовка каталога логов

```bash
sudo mkdir -p /opt/davaj_igrat/app/logs
sudo chown YOUR_USER:YOUR_USER /opt/davaj_igrat/app/logs
```

### 2.2. Права на скрипт запуска

```bash
chmod +x /opt/davaj_igrat/app/run_bot.sh
```

### 2.3. Редактирование unit-файла

Откройте `davaj_igrat_bot.service` и замените:

- `YOUR_USER` → ваше имя пользователя;
- при необходимости путь `/opt/davaj_igrat/app` на фактический путь к проекту.

### 2.4. Копирование unit-файла в systemd

```bash
sudo cp /opt/davaj_igrat/app/davaj_igrat_bot.service /etc/systemd/system/
```

### 2.5. Перезагрузка конфигурации systemd

```bash
sudo systemctl daemon-reload
```

### 2.6. Включение автозапуска при загрузке системы

```bash
sudo systemctl enable davaj_igrat_bot.service
```

### 2.7. Запуск сервиса

```bash
sudo systemctl start davaj_igrat_bot.service
```

### 2.8. Проверка статуса

```bash
sudo systemctl status davaj_igrat_bot.service
```

### 2.9. Просмотр логов

**Файлы логов (если в unit указан вывод в файл):**

```bash
tail -f /opt/davaj_igrat/app/logs/bot_stdout.log
tail -f /opt/davaj_igrat/app/logs/bot_stderr.log
```

**Через journald (если включены StandardOutput=journal / StandardError=journal):**

```bash
sudo journalctl -u davaj_igrat_bot.service -f
```

Полезные команды:

- Перезапуск: `sudo systemctl restart davaj_igrat_bot.service`
- Остановка: `sudo systemctl stop davaj_igrat_bot.service`
- Отключить автозапуск: `sudo systemctl disable davaj_igrat_bot.service`
