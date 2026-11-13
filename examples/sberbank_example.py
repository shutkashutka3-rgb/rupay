# rupay - СберБанк пример

from rupay import SberbankClient

# Инициализация (ключи из личного кабинета СберБанк)
client = SberbankClient(
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD"
)

# Регистрация заказа (создание платежа)
order = client.register_order(
    order_number="ORDER-12345",
    amount=150000,  # в копейках (1500.00 рублей)
    return_url="https://yoursite.com/payment/success",
    description="Оплата товара в интернет-магазине"
)

print(f"ID заказа: {order['order_id']}")
print(f"Ссылка для оплаты: {order['form_url']}")
print(f"Статус: {order['status']}")

# Проверка статуса заказа
status = client.get_order_status(order['order_id'])
print(f"\nТекущий статус: {status['status']}")
print(f"Оригинальный статус СберБанк: {status['original_status']}")
print(f"Сумма: {status['amount']} {status['currency']}")

# Отмена заказа (возврат средств)
# reverse = client.reverse_order(order['order_id'])
# print(f"Заказ отменен: {reverse}")

# Частичный возврат
# refund = client.refund_order(
#     order_id=order['order_id'],
#     amount=50000  # 500.00 рублей в копейках
# )
# print(f"Возврат выполнен: {refund}")

# Упрощенный вариант через единый интерфейс
simple_payment = client.create_payment(
    amount=1500.0,  # в рублях
    description="Простая оплата"
)
print(f"\n\nПростой платеж создан:")
print(f"ID: {simple_payment['id']}")
print(f"Ссылка: {simple_payment['confirmation_url']}")

print("\n✅ СберБанк интеграция работает!")
