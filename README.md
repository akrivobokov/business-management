# Business Management Prototype

Рабочий прототип Django-приложения для расчёта строительных заказов, логистики и управления товаром.

## Возможности
- API для расчёта стоимости заказа: `/orders/calculate/`
- API для создания заказа: `/orders/create/`
- Модели: Product, Order, Logistics
- Встроенная SQLite база данных
- Готово к деплою на Render, Heroku, PythonAnywhere

## Установка

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Автор

Created for demo purposes by [@akrivobokov](https://github.com/akrivobokov)