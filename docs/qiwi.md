# Работа с QIWI Wallet

## Получение токена

1. Войдите в QIWI кошелек: https://qiwi.com/
2. Перейдите в настройки → API → Создать токен
3. Укажите необходимые права доступа
4. Подробнее: https://developer.qiwi.com/

## Инициализация клиента

`python
from rupay import QiwiClient

client = QiwiClient(
    token="your_qiwi_token",
    phone="+79001234567"  # номер вашего QIWI кошелька
)
`

## Основные методы

### Проверка баланса

`python
balance = client.get_balance()
print(f"Баланс: {balance['amount']} {balance['currency']}")
`

### История платежей

`python
# Последние 10 операций
history = client.get_history(rows=10)

for tx in history:
    print(f"{tx['date']}: {tx['sum']} руб. - {tx['comment']}")

# С фильтрами
from datetime import datetime, timedelta

history = client.get_history(
    rows=50,
    operation="IN",  # только входящие (IN/OUT/ALL)
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)
`

### Отправка платежа на другой QIWI кошелек

`python
payment = client.send_payment(
    amount=500.0,
    recipient="+79009876543",
    comment="Перевод другу"
)

print(f"ID платежа: {payment['id']}")
print(f"Статус: {payment['status']}")
`

### Создание ссылки на оплату (QIWI P2P)

`python
payment = client.create_payment(
    amount=1000.0,
    description="Оплата товара",
    return_url="https://yoursite.com/success"
)

print(f"Ссылка для оплаты: {payment['confirmation_url']}")
`

## Async версия

`python
from rupay import AsyncQiwiClient
import asyncio

async def main():
    client = AsyncQiwiClient(
        token="your_token",
        phone="+79001234567"
    )
    
    balance = await client.get_balance()
    history = await client.get_history(rows=10)
    
    print(f"Баланс: {balance['amount']} руб.")

asyncio.run(main())
`

## Обработка ошибок

`python
from rupay import QiwiClient, AuthenticationError, PaymentError

try:
    client = QiwiClient(token="invalid", phone="+79001234567")
    balance = client.get_balance()
except AuthenticationError:
    print("Неверный токен или доступ запрещен!")
except PaymentError as e:
    print(f"Ошибка платежа: {e}")
`

## Права токена

При создании токена убедитесь, что выдали необходимые права:

- **Запрос информации о профиле кошелька** - для get_balance()
- **Просмотр истории платежей** - для get_history()
- **Проведение платежей без SMS** - для send_payment()

## Webhook уведомления (QIWI P2P)

Для получения уведомлений о платежах настройте webhook в личном кабинете QIWI.

Пример обработчика (Flask):

`python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)

@app.route('/qiwi/webhook', methods=['POST'])
def qiwi_webhook():
    # Проверка подписи (опционально)
    signature = request.headers.get('X-Api-Signature-SHA256')
    # secret_key = "your_webhook_secret"
    # expected = hmac.new(
    #     secret_key.encode(),
    #     request.data,
    #     hashlib.sha256
    # ).hexdigest()
    # 
    # if signature != expected:
    #     return "Invalid signature", 403
    
    data = request.json
    
    bill_id = data['bill']['billId']
    status = data['bill']['status']['value']
    amount = data['bill']['amount']['value']
    
    if status == 'PAID':
        print(f"Счет {bill_id} оплачен: {amount} руб.")
        # Обновите статус заказа
        # update_order_status(bill_id, 'paid')
    
    return "OK", 200
`

## Лимиты и ограничения

- Максимум 50 операций в истории за один запрос
- Минимальная сумма платежа: 1 рубль
- Комментарий до 255 символов
- Rate limit: ~100 запросов в минуту

## Частые проблемы

### Ошибка 401 (Unauthorized)
- Проверьте правильность токена
- Убедитесь, что токен не истек
- Проверьте права токена

### Ошибка 403 (Forbidden)
- Недостаточно прав у токена
- Аккаунт может быть ограничен

### История не возвращает операции
- Проверьте диапазон дат
- Убедитесь, что операции были в этот период
- Проверьте фильтры (operation, type)

## Полезные ссылки

- Документация API: https://developer.qiwi.com/
- Личный кабинет: https://qiwi.com/
- Создание токена: https://qiwi.com/api
- Поддержка: https://qiwi.com/support
