# Работа с Tinkoff Acquiring

## Получение ключей

1. Подключите Tinkoff Acquiring: https://www.tinkoff.ru/kassa/
2. В личном кабинете получите:
   - **Terminal Key** (ключ терминала)
   - **Secret Key** (секретный ключ для подписи)
3. Документация: https://www.tinkoff.ru/kassa/develop/api/

## Инициализация клиента

`python
from rupay import TinkoffClient

client = TinkoffClient(
    terminal_key="YOUR_TERMINAL_KEY",
    secret_key="YOUR_SECRET_KEY"
)
`

## Основные методы

### Создание платежа (Init)

`python
# Сумма указывается в КОПЕЙКАХ
payment = client.init_payment(
    amount=150000,  # 1500.00 рублей
    order_id="ORDER-12345",
    description="Оплата заказа в интернет-магазине"
)

print(f"ID платежа: {payment['PaymentId']}")
print(f"Ссылка для оплаты: {payment['PaymentURL']}")
print(f"Статус: {payment['Status']}")
`

### Проверка статуса платежа

`python
status = client.get_state(payment['PaymentId'])

print(f"Статус: {status['Status']}")  # succeeded/pending/canceled
print(f"Оригинальный статус: {status['OriginalStatus']}")  # CONFIRMED/NEW/etc
print(f"Сумма: {status['Amount']} копеек")
`

Статусы Tinkoff и их маппинг:
- NEW, AUTHORIZING, 3DS_CHECKING → pending
- CONFIRMED, PARTIAL_REFUNDED → succeeded
- REJECTED, CANCELED → canceled
- REFUNDED → efunded

### Подтверждение платежа (двухстадийная оплата)

Для двухстадийной оплаты нужно сначала авторизовать, потом подтвердить:

`python
# 1. Инициализация с авторизацией (деньги заблокированы)
payment = client.init_payment(
    amount=100000,
    order_id="ORDER-123",
    description="Заказ"
)

# 2. Подтверждение списания (когда товар отправлен)
confirm = client.confirm_payment(payment['PaymentId'])

# Можно подтвердить частичную сумму
confirm = client.confirm_payment(payment['PaymentId'], amount=50000)
`

### Отмена платежа

`python
# Полная отмена
cancel = client.cancel_payment(payment['PaymentId'])

# Частичная отмена
cancel = client.cancel_payment(payment['PaymentId'], amount=25000)
`

### Упрощенный интерфейс (совместимость)

Для единого API со всеми платежными системами:

`python
# Сумма в РУБЛЯХ (автоматически конвертируется в копейки)
payment = client.create_payment(
    amount=1500.0,
    description="Оплата заказа"
)

print(f"ID: {payment['id']}")
print(f"Ссылка: {payment['confirmation_url']}")

# Проверка статуса
status = client.get_payment_status(payment['id'])
print(f"Статус: {status['status']}")  # succeeded/pending/canceled
`

## Чек для 54-ФЗ

Для соблюдения 54-ФЗ нужно передавать данные чека:

`python
receipt = {
    "Email": "customer@example.com",
    "Phone": "+79001234567",
    "Taxation": "osn",  # система налогообложения
    "Items": [
        {
            "Name": "Товар 1",
            "Price": 100000,  # в копейках
            "Quantity": 1.0,
            "Amount": 100000,
            "Tax": "vat20",  # НДС 20%
            "PaymentMethod": "full_payment",
            "PaymentObject": "commodity"
        }
    ]
}

payment = client.init_payment(
    amount=100000,
    order_id="ORDER-123",
    description="Заказ",
    receipt=receipt
)
`

Системы налогообложения:
- osn — общая
- usn_income — УСН доход
- usn_income_outcome — УСН доход минус расход
- patent — патентная
- envd — ЕНВД
- esn — ЕСН

Ставки НДС:
- 
one — без НДС
- at0 — 0%
- at10 — 10%
- at20 — 20%
- at110 — расчетный 10/110
- at120 — расчетный 20/120

## Async версия

`python
from rupay import AsyncTinkoffClient
import asyncio

async def main():
    client = AsyncTinkoffClient(
        terminal_key="TERMINAL_KEY",
        secret_key="SECRET_KEY"
    )
    
    payment = await client.init_payment(
        amount=100000,
        order_id="ORDER-123",
        description="Async платеж"
    )
    
    status = await client.get_state(payment['PaymentId'])
    print(f"Статус: {status['Status']}")

asyncio.run(main())
`

## Обработка ошибок

`python
from rupay import TinkoffClient, AuthenticationError, PaymentError

try:
    client = TinkoffClient(
        terminal_key="invalid",
        secret_key="invalid"
    )
    payment = client.init_payment(amount=100, order_id="123", description="Test")
except AuthenticationError as e:
    print(f"Ошибка авторизации: {e}")
except PaymentError as e:
    print(f"Ошибка платежа: {e}")
`

## Webhook уведомления

Tinkoff отправляет уведомления о статусе на ваш сервер.

Пример обработчика (Flask):

`python
from flask import Flask, request
import hashlib

app = Flask(__name__)

SECRET_KEY = "your_secret_key"

def check_signature(data):
    """Проверка подписи от Tinkoff"""
    received_token = data.pop('Token', '')
    
    # Сортируем параметры и добавляем Password
    values = {**data, 'Password': SECRET_KEY}
    sorted_values = [str(values[key]) for key in sorted(values.keys()) if key not in ['Token']]
    
    # Вычисляем SHA-256
    token_string = ''.join(sorted_values)
    calculated_token = hashlib.sha256(token_string.encode()).hexdigest()
    
    return received_token == calculated_token

@app.route('/tinkoff/webhook', methods=['POST'])
def tinkoff_webhook():
    data = request.json
    
    # Проверяем подпись
    if not check_signature(data.copy()):
        return "Invalid signature", 403
    
    payment_id = data['PaymentId']
    status = data['Status']
    order_id = data['OrderId']
    amount = data['Amount']
    
    if status == 'CONFIRMED':
        print(f"Платеж {payment_id} для заказа {order_id} успешно оплачен: {amount/100} руб.")
        # Обновите статус заказа в БД
        # update_order_status(order_id, 'paid')
    elif status == 'REJECTED':
        print(f"Платеж {payment_id} отклонен")
        # update_order_status(order_id, 'failed')
    
    return "OK", 200
`

## Сохранение карты (рекуррентные платежи)

Для подписок и автоплатежей:

`python
# 1. Первый платеж с сохранением карты
payment = client.init_payment(
    amount=100000,
    order_id="SUBSCRIPTION-123",
    description="Подписка на месяц",
    customer_key="user_12345",  # уникальный ID клиента
    recurrent="Y"
)

# 2. Последующие платежи без ввода карты
payment = client.init_payment(
    amount=100000,
    order_id="SUBSCRIPTION-124",
    description="Продление подписки",
    customer_key="user_12345",
    recurrent="Y"
)
`

## Лимиты и ограничения

- Минимальная сумма: 100 копеек (1 рубль)
- Максимальная сумма: зависит от настроек терминала
- Описание платежа: до 250 символов
- Срок жизни ссылки на оплату: настраивается (по умолчанию 24 часа)

## Частые проблемы

### Ошибка подписи (Invalid Token)
- Проверьте правильность Secret Key
- Убедитесь, что сортируете параметры правильно
- Исключайте из подписи поля Token, Receipt, DATA, Shops

### Платеж зависает в статусе NEW
- Пользователь не завершил оплату
- Проблемы с 3D-Secure
- Истек срок действия ссылки

### Ошибка UNAUTHORIZED
- Неверный Terminal Key
- Терминал заблокирован
- Нет прав на операцию

## Тестовая среда

Для тестирования используйте тестовые ключи из личного кабинета.

Тестовые карты:
- **Успешная оплата**: 4300000000000777
- **Отклонение**: 4300000000000012
- **3DS**: 5200000000000007

CVV: любой  
Срок: любая будущая дата

## Полезные ссылки

- Документация: https://www.tinkoff.ru/kassa/develop/api/
- Личный кабинет: https://business.tinkoff.ru/
- Подключение: https://www.tinkoff.ru/kassa/
- Поддержка: https://www.tinkoff.ru/kassa/help/
