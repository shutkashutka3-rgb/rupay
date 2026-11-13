# rupay

[![PyPI version](https://badge.fury.io/py/rupay.svg)](https://badge.fury.io/py/rupay)
[![Python Versions](https://img.shields.io/pypi/pyversions/rupay.svg)](https://pypi.org/project/rupay/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Единая Python-библиотека для работы с российскими платежными системами**

Простая интеграция с ЮMoney (Яндекс.Деньги), QIWI и Tinkoff через единый интерфейс.

---

## 🚀 Возможности

- **Единый API** для всех платежных систем
- **Async/await поддержка** для высокой производительности
- **Type hints** для удобной разработки
- **Простая интеграция** — всего несколько строк кода
- **Webhook обработка** для автоматизации
- **Подробная документация** на русском языке

## 📦 Установка

`ash
pip install rupay
`

## 🔧 Быстрый старт

### ЮMoney (Яндекс.Деньги)

`python
from rupay import YooMoneyClient

# Инициализация клиента
client = YooMoneyClient(token="your_token_here")

# Создание платежа
payment = client.create_payment(
    amount=100.0,
    description="Оплата заказа #123",
    return_url="https://yoursite.com/success"
)
print(f"Ссылка для оплаты: {payment['confirmation_url']}")

# Проверка статуса
status = client.get_payment_status(payment['id'])
print(f"Статус: {status['status']}")
`

### QIWI

`python
from rupay import QiwiClient

# Инициализация
client = QiwiClient(token="your_qiwi_token", phone="+79001234567")

# Проверка баланса
balance = client.get_balance()
print(f"Баланс: {balance['amount']} {balance['currency']}")

# История операций
history = client.get_history(rows=10)
for transaction in history:
    print(f"{transaction['date']}: {transaction['sum']} руб.")
`

### Tinkoff Acquiring

`python
from rupay import TinkoffClient

# Инициализация
client = TinkoffClient(
    terminal_key="your_terminal_key",
    secret_key="your_secret_key"
)

# Создание платежа
payment = client.init_payment(
    amount=150000,  # сумма в копейках (1500.00 руб)
    order_id="ORDER-123",
    description="Оплата товара"
)
print(f"Ссылка: {payment['PaymentURL']}")

# Проверка статуса
status = client.get_state(payment['PaymentId'])
print(f"Статус: {status['Status']}")
`

## 🔄 Async версия

Все клиенты поддерживают асинхронную работу:

`python
from rupay import AsyncYooMoneyClient
import asyncio

async def main():
    client = AsyncYooMoneyClient(token="your_token")
    payment = await client.create_payment(
        amount=100.0,
        description="Async платеж"
    )
    print(payment)

asyncio.run(main())
`

## 📚 Документация

Полная документация доступна в папке [docs/](docs/):

- [Руководство по ЮMoney](docs/yoomoney.md)
- [Руководство по QIWI](docs/qiwi.md)
- [Руководство по Tinkoff](docs/tinkoff.md)
- [Обработка Webhook](docs/webhooks.md)
- [Примеры использования](examples/)

## 🎯 Зачем rupay?

### Проблема
Каждая платежная система имеет свой API:
- Разные форматы запросов
- Разная документация
- Разные методы обработки ошибок
- Много времени на интеграцию каждой системы

### Решение
**rupay** — единый интерфейс для всех систем:
`python
# Одинаковый код для всех платежных систем
for client in [yoomoney_client, qiwi_client, tinkoff_client]:
    payment = client.create_payment(amount=100, description="Тест")
    status = client.get_payment_status(payment['id'])
`

## 🛠️ Требования

- Python 3.7+
- requests >= 2.25.0
- aiohttp >= 3.7.0 (для async версии)

## 🤝 Поддержка проекта

Если библиотека помогла вам сэкономить время, поддержите разработку:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink)](https://github.com/sponsors/shutkashutka3-rgb)

Ваши донаты помогают:
- Поддерживать библиотеку актуальной
- Добавлять новые платежные системы
- Улучшать документацию
- Быстрее отвечать на issues

## 📄 Лицензия

MIT License — используйте свободно в любых проектах.

## 🐛 Нашли баг?

Создайте [issue](https://github.com/shutkashutka3-rgb/rupay/issues) с описанием проблемы.

## ✨ Roadmap

- [ ] Поддержка ЮKassa (CloudPayments)
- [ ] Сбербанк Acquiring API
- [ ] Webhook валидация для всех систем
- [ ] CLI инструмент для быстрой проверки
- [ ] Плагины для Django/Flask

---

**Made with ❤️ for Russian developers**

