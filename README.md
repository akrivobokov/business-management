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

## Автор

Created for demo purposes by [@akrivobokov](https://github.com/akrivobokov)
