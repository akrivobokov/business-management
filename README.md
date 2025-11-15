# Business Management Prototype

Рабочий прототип Django-приложения для расчёта строительных заказов, логистики и управления товаром.

## Возможности
- API для расчёта стоимости заказа: `/orders/calculate/`
- API для создания заказа: `/orders/create/`
- Модели: Product, Order, Logistics
- Калькулятор декомпозиции прибыли: `/business-calculator/`
  - поддерживает ввод рентабельности, автоматический расчёт себестоимости и выручки с учётом выбранной СНО
- Встроенная SQLite база данных
- Готово к деплою на Render, Heroku, PythonAnywhere

## Обновление регуляторных данных

Калькулятор использует актуальные справочники организационно-правовых форм и систем налогообложения РФ.
Запустите ежедневный джоб, который подтянет данные с портала ФНС и обновит кэш `regulations_cache.json`:

```bash
python manage.py refresh_regulatory_data
```

На Linux можно добавить cron-задание, выполняющее команду раз в сутки, чтобы таблицы автоматически сверялись с официальными источниками.

## Установка

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Conda/Mamba окружение (опционально)

Если вы запускаете проект на GitHub Actions, в облаке или просто предпочитаете Conda/Mamba,
воспользуйтесь подготовленным `environment.yml` в корне репозитория:

```bash
conda env create -f environment.yml
conda activate business-management
python manage.py migrate
python run_online.py --host 0.0.0.0 --port 8000
```

Файл содержит те же зависимости, что и `requirements.txt`, поэтому обе инструкции взаимозаменяемы
— выбирайте тот вариант, который проще встроить в вашу инфраструктуру.

## Запуск на любом компьютере

Ниже приведён пошаговый сценарий, который одинаково работает на Windows, macOS и Linux.

1. **Установите Python 3.11+**. На Windows скачайте дистрибутив с python.org и поставьте галочку "Add Python to PATH". На macOS и Linux Python обычно уже доступен (проверьте `python3 --version`).
2. **Склонируйте проект** и перейдите в папку: `git clone https://github.com/<your-account>/business-management.git && cd business-management`.
3. **Создайте виртуальное окружение** (по желанию, но так проще поддерживать зависимости):
   - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows PowerShell: `python -m venv .venv; .\.venv\Scripts\Activate.ps1`
4. **Установите зависимости**: `pip install -r requirements.txt`.
5. **Примените миграции**: `python manage.py migrate`.
6. **(Опционально) обновите справочники ОПФ и СНО** из официальных источников ФНС: `python manage.py refresh_regulatory_data`.
7. **Запустите приложение онлайн** командой `python run_online.py --host 0.0.0.0 --port 8000` (по умолчанию откроется порт 8000, при необходимости укажите другой).
8. **Откройте калькулятор** из любого браузера по адресу `http://<IP_вашего_компьютера>:8000/business-calculator/`. Если запускаете локально, используйте `http://127.0.0.1:8000/business-calculator/`.

Эти действия не требуют специфических инструментов, поэтому одинаково воспроизводятся на домашнем ноутбуке, офисном ПК или сервере в облаке.

### Быстрый онлайн-запуск

Чтобы сразу получить онлайн-доступ (например, на VPS, в Docker-контейнере или на облачном сервере),
используйте обёртку над `runserver` — она по умолчанию биндится к `0.0.0.0` и открывает порт 8000:

```bash
python run_online.py --host 0.0.0.0 --port 8000
```

После запуска страница калькулятора будет доступна по адресу `http://<ваш_сервер>:8000/business-calculator/`.

### Быстрый офлайн-расчёт

Если нужен расчёт без запуска веб-сервера, воспользуйтесь CLI-обёрткой:

```bash
python run_calculator.py --monthly-profit 200000 --margin-percent 35 --days-in-month 22
```

Скрипт использует те же справочники ОПФ и СНО, что и веб-страница, поэтому цифры будут идентичны. Аргументы опциональны — по умолчанию берутся значения из интерфейса калькулятора.

## Автор

Created for demo purposes by [@akrivobokov](https://github.com/akrivobokov)
