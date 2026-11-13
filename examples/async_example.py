# Async пример - работа со всеми системами одновременно

import asyncio
from rupay import AsyncYooMoneyClient, AsyncQiwiClient, AsyncTinkoffClient


async def process_payments():
    # Инициализация клиентов
    yoomoney = AsyncYooMoneyClient(token="YOOMONEY_TOKEN")
    qiwi = AsyncQiwiClient(token="QIWI_TOKEN", phone="+79001234567")
    tinkoff = AsyncTinkoffClient(
        terminal_key="TINKOFF_TERMINAL",
        secret_key="TINKOFF_SECRET"
    )
    
    # Параллельное создание платежей во всех системах
    print("Создаем платежи параллельно...")
    
    payments = await asyncio.gather(
        yoomoney.create_payment(amount=100.0, description="ЮMoney платеж"),
        qiwi.create_payment(amount=200.0, description="QIWI платеж"),
        tinkoff.create_payment(amount=300.0, description="Tinkoff платеж"),
        return_exceptions=True
    )
    
    print("\nРезультаты:")
    for i, payment in enumerate(payments):
        if isinstance(payment, Exception):
            print(f"Платеж {i+1}: Ошибка - {payment}")
        else:
            print(f"Платеж {i+1}: ID {payment.get('id')}, URL: {payment.get('confirmation_url')}")
    
    # Параллельная проверка балансов
    print("\n\nПроверяем балансы параллельно...")
    
    balances = await asyncio.gather(
        yoomoney.get_balance(),
        qiwi.get_balance(),
        return_exceptions=True
    )
    
    print(f"ЮMoney баланс: {balances[0].get('amount', 'Ошибка')} руб.")
    print(f"QIWI баланс: {balances[1].get('amount', 'Ошибка')} руб.")


if __name__ == "__main__":
    asyncio.run(process_payments())
