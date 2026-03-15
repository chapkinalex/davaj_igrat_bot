#!/usr/bin/env bash
# Развёртывание бота на Ubuntu: apt, venv, systemd.
# Запуск: ./deploy_on_server.sh ИМЯ_ПОЛЬЗОВАТЕЛЯ
# Пример: ./deploy_on_server.sh ubuntu

set -e

if [ -z "$1" ]; then
    echo "Укажите имя пользователя Linux. Пример: ./deploy_on_server.sh ubuntu"
    exit 1
fi

USERNAME="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 0. Системные зависимости (apt) ==="
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip

echo "=== 1. Виртуальное окружение и pip ==="
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "=== 2. Каталог логов и права ==="
mkdir -p logs
chmod +x run_bot.sh
sudo chown "$USERNAME:$USERNAME" logs

echo "=== 3. Файл .env ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Создан .env из шаблона. ОБЯЗАТЕЛЬНО откройте .env и впишите свой BOT_TOKEN!"
else
    echo "Файл .env уже есть."
fi

echo "=== 4. Unit systemd ==="
sed -e "s/YOUR_USER/$USERNAME/g" -e "s|/home/ubuntu/davai_sigrai_bot|$SCRIPT_DIR|g" davaj_igrat_bot.service > /tmp/davaj_igrat_bot.service
sudo cp /tmp/davaj_igrat_bot.service /etc/systemd/system/
rm -f /tmp/davaj_igrat_bot.service

echo "=== 5. Включение и запуск сервиса ==="
sudo systemctl daemon-reload
sudo systemctl enable davaj_igrat_bot.service
sudo systemctl start davaj_igrat_bot.service

echo ""
echo "Готово. Проверка: sudo systemctl status davaj_igrat_bot.service"
echo ""
echo "Если бот не запустится — откройте .env и впишите BOT_TOKEN=ваш_токен, затем:"
echo "  sudo systemctl restart davaj_igrat_bot.service"
