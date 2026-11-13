# rupay

from rupay import YooMoneyClient

# Инициализация клиента
client = YooMoneyClient(token="YOUR_YOOMONEY_TOKEN")

# Создание платежа
payment = client.create_payment(
    amount=500.0,
    description="Оплата товара",
    return_url="https://yoursite.com/payment/success"
)

print(f"ID платежа: {payment['id']}")
print(f"Ссылка для оплаты: {payment['confirmation_url']}")

# Проверка статуса
status = client.get_payment_status(payment['id'])
print(f"Статус платежа: {status['status']}")

# Получение баланса
balance = client.get_balance()
print(f"Баланс: {balance['amount']} {balance['currency']}")

# История операций
history = client.get_operation_history(records=5)
for operation in history:
    print(f"Операция {operation.get('operation_id')}: {operation.get('amount')} руб.")
