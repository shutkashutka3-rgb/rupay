# rupay - Tinkoff пример

from rupay import TinkoffClient

# Инициализация (ключи из личного кабинета Tinkoff Acquiring)
client = TinkoffClient(
    terminal_key="YOUR_TERMINAL_KEY",
    secret_key="YOUR_SECRET_KEY"
)

# Создание платежа (сумма в копейках)
payment = client.init_payment(
    amount=150000,  # 1500.00 рублей
    order_id="ORDER-12345",
    description="Оплата заказа в интернет-магазине"
)

print(f"ID платежа: {payment['PaymentId']}")
print(f"Ссылка для оплаты: {payment['PaymentURL']}")
print(f"Статус: {payment['Status']}")

# Проверка статуса
status = client.get_state(payment['PaymentId'])
print(f"\nТекущий статус: {status['Status']}")
print(f"Оригинальный статус Tinkoff: {status['OriginalStatus']}")

# Подтверждение платежа (для двухстадийной оплаты)
# confirm = client.confirm_payment(payment['PaymentId'])
# print(f"Платеж подтвержден: {confirm}")

# Отмена платежа
# cancel = client.cancel_payment(payment['PaymentId'])
# print(f"Платеж отменен: {cancel}")

# Упрощенный вариант через единый интерфейс
simple_payment = client.create_payment(
    amount=500.0,  # в рублях
    description="Простая оплата"
)
print(f"\n\nПростой платеж создан:")
print(f"ID: {simple_payment['id']}")
print(f"Ссылка: {simple_payment['confirmation_url']}")
