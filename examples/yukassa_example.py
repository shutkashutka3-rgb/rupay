# rupay - ЮKassa пример

from rupay import YuKassaClient

# Инициализация (ключи из личного кабинета ЮKassa)
client = YuKassaClient(
    shop_id="YOUR_SHOP_ID",
    secret_key="YOUR_SECRET_KEY"
)

# Создание платежа
payment = client.create_payment(
    amount=500.0,  # в рублях
    description="Оплата заказа #12345",
    return_url="https://yoursite.com/payment/success",
    metadata={"order_id": "12345", "customer_id": "67890"}
)

print(f"ID платежа: {payment['id']}")
print(f"Ссылка для оплаты: {payment['confirmation_url']}")
print(f"Статус: {payment['status']}")

# Проверка статуса платежа
status = client.get_payment_status(payment['id'])
print(f"\nТекущий статус: {status['status']}")
print(f"Оплачено: {status['paid']}")
print(f"Сумма: {status['amount']} {status['currency']}")

# Подтверждение платежа (для двухстадийной оплаты)
# confirm = client.capture_payment(payment['id'])
# print(f"Платеж подтвержден: {confirm}")

# Отмена платежа
# cancel = client.cancel_payment(payment['id'])
# print(f"Платеж отменен: {cancel}")

# Возврат средств
# refund = client.create_refund(
#     payment_id=payment['id'],
#     amount=100.0,
#     description="Частичный возврат"
# )
# print(f"Возврат создан: {refund}")

print("\n✅ ЮKassa интеграция работает!")
