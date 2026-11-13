# rupay - QIWI пример

from rupay import QiwiClient

# Инициализация (номер телефона в любом формате)
client = QiwiClient(
    token="YOUR_QIWI_TOKEN",
    phone="+79001234567"
)

# Проверка баланса
balance = client.get_balance()
print(f"Баланс QIWI: {balance['amount']} {balance['currency']}")

# История последних операций
print("\nПоследние 10 операций:")
history = client.get_history(rows=10)
for tx in history:
    print(f"{tx['date']}: {tx['sum']} руб. - {tx['comment']}")

# Отправка денег на другой QIWI кошелек
payment = client.send_payment(
    amount=100.0,
    recipient="+79009876543",
    comment="Перевод другу"
)
print(f"\nПеревод выполнен. ID: {payment['id']}, статус: {payment['status']}")

# Создание ссылки для оплаты (для единого интерфейса)
invoice = client.create_payment(
    amount=250.0,
    description="Оплата услуги",
    return_url="https://yoursite.com/success"
)
print(f"\nСсылка для оплаты: {invoice['confirmation_url']}")
