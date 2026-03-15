# Запуск бота на сервере через GitHub

Два этапа: (1) залить проект в GitHub с компьютера, (2) на сервере склонировать и запустить.

---

## ЭТАП 1. Залить проект в GitHub (с вашего компьютера)

### 1.1. Создать репозиторий на GitHub (если ещё нет)

1. Зайдите на https://github.com и войдите в аккаунт.
2. Нажмите зелёную кнопку **New** (или **+** → **New repository**).
3. **Repository name:** например `davai_sigrai_bot`.
4. Оставьте **Public**, галочку **Add a README** можно не ставить.
5. Нажмите **Create repository**.
6. На открывшейся странице скопируйте **ссылку на репозиторий** — она вида `https://github.com/ВАШ_ЛОГИН/davai_sigrai_bot.git`. Она понадобится ниже.

### 1.2. Отправить код с компьютера в этот репозиторий

1. Откройте в Cursor **вашу локальную папку с ботом** (та, что на рабочем столе: «Давай играть» → `davai_sigrai_bot`).
2. Откройте терминал в Cursor: **Terminal → New Terminal** (или **Ctrl+`**).
3. Проверьте, что вы в папке проекта. Введите по очереди:

   ```bash
   git status
   ```
   Если пишет «not a git repository» — инициализируйте:
   ```bash
   git init
   ```

4. Добавьте удалённый репозиторий (подставьте **вашу** ссылку из шага 1.1):
   ```bash
   git remote add origin https://github.com/ВАШ_ЛОГИН/davai_sigrai_bot.git
   ```
   Если уже есть `origin` и нужно заменить ссылку:
   ```bash
   git remote set-url origin https://github.com/ВАШ_ЛОГИН/davai_sigrai_bot.git
   ```

5. Добавьте все файлы и сделайте коммит:
   ```bash
   git add .
   git commit -m "Проект бота для сервера"
   ```

6. Отправьте в GitHub (ветка может называться main или master):
   ```bash
   git branch -M main
   git push -u origin main
   ```
   Если попросит логин и пароль GitHub — введите. Для пароля сейчас часто нужен **Personal Access Token** (GitHub → Settings → Developer settings → Personal access tokens → создать токен с правом repo). Вместо пароля вставьте этот токен.

7. Обновите страницу репозитория на GitHub — там должны появиться ваши файлы. Этап 1 завершён.

---

## ЭТАП 2. На сервере: склонировать и запустить бота

### 2.1. Подключиться к серверу в Cursor

1. **Ctrl+Shift+P** → введите **connect to host** → выберите **Remote-SSH: Connect to Host...**.
2. Введите **логин@адрес_сервера** (например `ubuntu@ваш-сервер.ru`) → Enter.
3. В новом окне выберите **Linux**, введите пароль от сервера.
4. Дождитесь надписи внизу слева **SSH: логин@адрес**.

### 2.2. Открыть домашнюю папку на сервере

1. **Ctrl+Shift+P** → **open folder** → **File: Open Folder...**.
2. Введите путь: **`/home/ubuntu`** (или `/home/ваш_логин`, если логин другой) → Enter.

### 2.3. Склонировать репозиторий на сервер

1. Откройте терминал: **Terminal → New Terminal** (или **Ctrl+`**).
2. Введите (подставьте **вашу** ссылку и при необходимости другой логин в пути):
   ```bash
   cd /home/ubuntu
   git clone https://github.com/ВАШ_ЛОГИН/davai_sigrai_bot.git davai_sigrai_bot
   ```
   Пример: `git clone https://github.com/ivan/davai_sigrai_bot.git davai_sigrai_bot`
3. Если репозиторий приватный — попросит логин и пароль (или токен) GitHub. Введите их.
4. После выполнения появится папка **davai_sigrai_bot**.

### 2.4. Открыть папку с ботом в Cursor

1. **File → Open Folder...**.
2. Введите: **`/home/ubuntu/davai_sigrai_bot`** (или ваш путь) → OK.
3. В левой панели должны быть файлы: main.py, bot, config, data, run_bot.sh, deploy_on_server.sh и т.д.

### 2.5. Запустить скрипт установки

1. В терминале внизу введите:
   ```bash
   whoami
   ```
   Запомните вывод (например `ubuntu`).

2. Выполните:
   ```bash
   chmod +x deploy_on_server.sh
   ./deploy_on_server.sh ubuntu
   ```
   (вместо `ubuntu` подставьте то, что показал `whoami`). Введите пароль сервера, если попросит.

### 2.6. Вписать токен бота

1. В левой панели откройте файл **.env** (если нет — откройте **.env.example**, сохраните как **.env**).
2. Замените `your_bot_token_here` на **ваш токен** от @BotFather. Сохраните (**Ctrl+S**).
3. В терминале выполните:
   ```bash
   sudo systemctl restart davaj_igrat_bot.service
   ```
   Введите пароль сервера, если попросит.

### 2.7. Проверить

Введите:
```bash
sudo systemctl status davaj_igrat_bot.service
```
Должно быть **active (running)**. Тогда бот уже работает на сервере.

---

## Если что-то пошло не так

- **Ошибка при git push (этап 1):** проверьте ссылку `origin` и что репозиторий создан на GitHub. Для пароля используйте Personal Access Token, если обычный пароль не принимают.
- **Ошибка при git clone (этап 2):** проверьте ссылку и что на сервере установлен git: `sudo apt install git -y`.
- **Бот не запускается:** выполните `tail -30 /home/ubuntu/davai_sigrai_bot/logs/bot_stderr.log` и посмотрите текст ошибки (или пришлите его — подскажу, что исправить).
