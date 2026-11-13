# rupay

[![PyPI version](https://badge.fury.io/py/rupay.svg)](https://badge.fury.io/py/rupay)
[![Python Versions](https://img.shields.io/pypi/pyversions/rupay.svg)](https://pypi.org/project/rupay/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Единая Python-библиотека для работы с российскими платежными системами**

Простая интеграция с ЮMoney, QIWI, Tinkoff, ЮKassa и СберБанк через единый интерфейс.

---

## 💰 Поддержите проект

**Если библиотека сэкономила ваше время — поддержите разработку!**

<div align="center">
  <a href="https://www.donationalerts.com/r/oxykid">
    <img src="https://img.shields.io/badge/💸_Поддержать-DonationAlerts-F15A22?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAQAAAC1QeVaAAAAUklEQVR42mNgGAWjgP6ASdncAEwH/8fhiP//wXTw/3+MThD9/x9MB/+HmwPXCRUH08H/kXRC5cF08H+MOqHyYDr4PxZxVHmMOqHyYDr4PwMAq1lPfr3bTQQAAAAASUVORK5CYII=" alt="DonationAlerts" width="200">
  </a>
  
  <br><br>
  
  <p><b>Ваши донаты помогают:</b></p>
  <p>✅ Поддерживать библиотеку актуальной<br>
  ✅ Добавлять новые платежные системы<br>
  ✅ Улучшать документацию<br>
  ✅ Быстрее отвечать на issues</p>
</div>

---

## 🚀 Возможности

- **Единый API** для всех платежных систем
- **5 платежных систем**: ЮMoney, QIWI, Tinkoff, ЮKassa, СберБанк
- **Async/await поддержка** для высокой производительности
- **Type hints** для удобной разработки
- **Простая интеграция** — всего несколько строк кода
- **Webhook обработка** для автоматизации
- **Подробная документация** на русском языке

## 📦 Установка

```bash
pip install rupay
```

## 🔧 Быстрый старт

### ЮMoney (Яндекс.Деньги)

```python
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
```

### QIWI

```python
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
```

### Tinkoff Acquiring

```python
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
```

### ЮKassa 🆕

```python
from rupay import YuKassaClient

# Инициализация
client = YuKassaClient(
    shop_id="your_shop_id",
    secret_key="your_secret_key"
)

# Создание платежа
payment = client.create_payment(
    amount=500.0,
    description="Оплата заказа",
    return_url="https://yoursite.com/success"
)
print(f"Ссылка: {payment['confirmation_url']}")

# Проверка статуса
status = client.get_payment_status(payment['id'])
print(f"Статус: {status['status']}, Оплачено: {status['paid']}")
```

### СберБанк 🆕

```python
from rupay import SberbankClient

# Инициализация
client = SberbankClient(
    username="your_username",
    password="your_password"
)

# Создание платежа
payment = client.create_payment(
    amount=1000.0,
    description="Оплата заказа",
    return_url="https://yoursite.com/success"
)
print(f"Ссылка: {payment['confirmation_url']}")

# Проверка статуса
status = client.get_payment_status(payment['id'])
print(f"Статус: {status['status']}")
```

## 🔄 Async версия

Все клиенты поддерживают асинхронную работу:

```python
from rupay import AsyncYuKassaClient, AsyncSberbankClient
import asyncio

async def main():
    # ЮKassa
    yukassa = AsyncYuKassaClient(shop_id="...", secret_key="...")
    payment = await yukassa.create_payment(amount=100.0, description="Test")
    
    # СберБанк
    sber = AsyncSberbankClient(username="...", password="...")
    order = await sber.create_payment(amount=200.0, description="Order")
    
    print(payment, order)

asyncio.run(main())
```

## 📚 Документация

Полная документация доступна в папке [docs/](docs/):

- [Руководство по ЮMoney](docs/yoomoney.md)
- [Руководство по QIWI](docs/qiwi.md)
- [Руководство по Tinkoff](docs/tinkoff.md)
- [Руководство по ЮKassa](docs/yukassa.md) 🆕
- [Руководство по СберБанк](docs/sberbank.md) 🆕
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
```python
# Одинаковый код для всех платежных систем
for client in [yoomoney, qiwi, tinkoff, yukassa, sberbank]:
    payment = client.create_payment(amount=100, description="Тест")
    status = client.get_payment_status(payment['id'])
```

## 🛠️ Требования

- Python 3.7+
- requests >= 2.25.0
- aiohttp >= 3.7.0 (для async версии)

## 🎉 Что нового в v0.2.0

- ✅ Добавлена поддержка **ЮKassa** (YooKassa)
- ✅ Добавлена поддержка **СберБанк Acquiring**
- ✅ Синхронные и асинхронные версии для новых систем
- ✅ Единый интерфейс create_payment() для всех систем
- ✅ Примеры использования и документация

## 📄 Лицензия

MIT License — используйте свободно в любых проектах.

## 🐛 Нашли баг?

Создайте [issue](https://github.com/shutkashutka3-rgb/rupay/issues) с описанием проблемы.

## ✨ Roadmap

- [x] ЮKassa (YooKassa) ✅
- [x] СберБанк Acquiring ✅
- [ ] Webhook валидация для всех систем
- [ ] CLI инструмент для быстрой проверки
- [ ] Плагины для Django/Flask
- [ ] Alfa-Bank Acquiring API

---

**Made with ❤️ for Russian developers**
