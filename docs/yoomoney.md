# Работа с ЮMoney (Яндекс.Деньги)

## Получение токена

1. Зарегистрируйте приложение на https://yoomoney.ru/myservices/new
2. Получите OAuth токен через процесс авторизации
3. Подробнее: https://yoomoney.ru/docs/wallet

## Инициализация клиента

`python
from rupay import YooMoneyClient

client = YooMoneyClient(token="your_yoomoney_token")
`

## Основные методы

### Информация об аккаунте

`python
info = client.get_account_info()
print(f"Номер счета: {info['account']}")
print(f"Баланс: {info['balance']} {info['currency']}")
`

### Создание платежа

`python
payment = client.create_payment(
    amount=500.0,
    description="Оплата товара #123",
    return_url="https://yoursite.com/success",
    label="order-123"  # метка для идентификации
)

print(f"Ссылка для оплаты: {payment['confirmation_url']}")
`

### Проверка статуса платежа

`python
status = client.get_payment_status(payment['id'])

if status['status'] == 'succeeded':
    print("Платеж успешно выполнен!")
elif status['status'] == 'pending':
    print("Платеж в обработке")
else:
    print("Платеж отклонен")
`

### История операций

`python
from datetime import datetime, timedelta

# Последние 30 операций
history = client.get_operation_history(records=30)

# С фильтрами
history = client.get_operation_history(
    type="deposition",  # только пополнения
    label="order-",     # по метке
    from_date=datetime.now() - timedelta(days=7),
    records=50
)

for operation in history:
    print(f"{operation['datetime']}: {operation['amount']} руб.")
`

### Получение баланса

`python
balance = client.get_balance()
print(f"Текущий баланс: {balance['amount']} {balance['currency']}")
`

## Async версия

`python
from rupay import AsyncYooMoneyClient
import asyncio

async def main():
    client = AsyncYooMoneyClient(token="your_token")
    
    # Все методы идентичны, но с await
    balance = await client.get_balance()
    payment = await client.create_payment(amount=100, description="Async платеж")
    status = await client.get_payment_status(payment['id'])

asyncio.run(main())
`

## Обработка ошибок

`python
from rupay import YooMoneyClient, AuthenticationError, PaymentError

try:
    client = YooMoneyClient(token="invalid_token")
    payment = client.create_payment(amount=100, description="Test")
except AuthenticationError:
    print("Неверный токен!")
except PaymentError as e:
    print(f"Ошибка платежа: {e}")
`

## Webhook уведомления

ЮMoney отправляет уведомления о статусе платежей на ваш сервер.

Пример обработчика (Flask):

`python
from flask import Flask, request
import hashlib

app = Flask(__name__)

@app.route('/yoomoney/webhook', methods=['POST'])
def yoomoney_webhook():
    data = request.form.to_dict()
    
    # Проверка подписи (опционально)
    # notification_secret = "your_secret"
    # sha1_hash = hashlib.sha1(
    #     f"{data['notification_type']}&{data['operation_id']}&{data['amount']}&"
    #     f"{data['currency']}&{data['datetime']}&{data['sender']}&"
    #     f"{data['codepro']}&{notification_secret}&{data['label']}"
    #     .encode()
    # ).hexdigest()
    # 
    # if sha1_hash != data['sha1_hash']:
    #     return "Invalid signature", 403
    
    # Обработка платежа
    operation_id = data['operation_id']
    amount = data['amount']
    label = data.get('label', '')
    
    print(f"Получен платеж {operation_id}: {amount} руб., метка: {label}")
    
    # Обновите статус заказа в вашей БД
    # update_order_status(label, 'paid')
    
    return "OK", 200
`

## Лимиты и ограничения

- Максимум 100 операций в истории за один запрос
- Описание платежа до 128 символов
- Минимальная сумма платежа: 1 рубль
- Rate limit: уточняйте в документации ЮMoney

## Полезные ссылки

- Документация API: https://yoomoney.ru/docs/wallet
- Личный кабинет: https://yoomoney.ru/myservices/
- Служба поддержки: https://yoomoney.ru/page?id=536884
