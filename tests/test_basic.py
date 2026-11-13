"""
Базовые тесты для rupay
"""

import pytest
from rupay import (
    YooMoneyClient,
    QiwiClient,
    TinkoffClient,
    ValidationError,
    AuthenticationError
)


def test_yoomoney_init():
    """Тест инициализации YooMoney клиента"""
    client = YooMoneyClient(token="test_token")
    assert client.token == "test_token"
    assert client.timeout == 30


def test_yoomoney_empty_token():
    """Тест на пустой токен"""
    with pytest.raises(ValidationError):
        YooMoneyClient(token="")


def test_qiwi_init():
    """Тест инициализации QIWI клиента"""
    client = QiwiClient(token="test_token", phone="+79001234567")
    assert client.token == "test_token"
    assert client.phone == "79001234567"


def test_qiwi_phone_formatting():
    """Тест форматирования номера телефона"""
    client = QiwiClient(token="test", phone="+7 900 123-45-67")
    assert client.phone == "79001234567"


def test_tinkoff_init():
    """Тест инициализации Tinkoff клиента"""
    client = TinkoffClient(terminal_key="test_terminal", secret_key="test_secret")
    assert client.terminal_key == "test_terminal"
    assert client.secret_key == "test_secret"


def test_tinkoff_token_generation():
    """Тест генерации токена для подписи"""
    client = TinkoffClient(terminal_key="TestTerminal", secret_key="TestSecret")
    
    data = {
        "TerminalKey": "TestTerminal",
        "Amount": "100000",
        "OrderId": "ORDER-123"
    }
    
    token = client._generate_token(data)
    assert isinstance(token, str)
    assert len(token) == 64  # SHA-256 хеш


def test_validation_errors():
    """Тест валидации входных данных"""
    client = YooMoneyClient(token="test")
    
    with pytest.raises(ValidationError, match="Сумма должна быть больше 0"):
        client.create_payment(amount=-100, description="Test")
    
    with pytest.raises(ValidationError, match="Сумма должна быть больше 0"):
        client.create_payment(amount=0, description="Test")


@pytest.mark.asyncio
async def test_async_yoomoney_init():
    """Тест асинхронного YooMoney клиента"""
    from rupay import AsyncYooMoneyClient
    
    client = AsyncYooMoneyClient(token="test_token")
    assert client.token == "test_token"


@pytest.mark.asyncio
async def test_async_qiwi_init():
    """Тест асинхронного QIWI клиента"""
    from rupay import AsyncQiwiClient
    
    client = AsyncQiwiClient(token="test_token", phone="+79001234567")
    assert client.phone == "79001234567"


@pytest.mark.asyncio
async def test_async_tinkoff_init():
    """Тест асинхронного Tinkoff клиента"""
    from rupay import AsyncTinkoffClient
    
    client = AsyncTinkoffClient(terminal_key="test", secret_key="secret")
    assert client.terminal_key == "test"


def test_imports():
    """Тест импорта всех модулей"""
    from rupay import (
        YooMoneyClient,
        AsyncYooMoneyClient,
        QiwiClient,
        AsyncQiwiClient,
        TinkoffClient,
        AsyncTinkoffClient,
        RupayError,
        AuthenticationError,
        PaymentError,
        NetworkError,
        ValidationError
    )
    
    assert YooMoneyClient is not None
    assert AsyncYooMoneyClient is not None
    assert QiwiClient is not None
    assert AsyncQiwiClient is not None
    assert TinkoffClient is not None
    assert AsyncTinkoffClient is not None
    assert RupayError is not None
