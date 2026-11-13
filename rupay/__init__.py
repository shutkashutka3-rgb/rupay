"""
rupay - Единая библиотека для работы с российскими платежными системами
"""

__version__ = "0.1.0"
__author__ = "rupay contributors"
__license__ = "MIT"

from .yoomoney import YooMoneyClient, AsyncYooMoneyClient
from .qiwi import QiwiClient, AsyncQiwiClient
from .tinkoff import TinkoffClient, AsyncTinkoffClient
from .exceptions import (
    RupayError,
    AuthenticationError,
    PaymentError,
    NetworkError,
    ValidationError
)

__all__ = [
    # ЮMoney
    "YooMoneyClient",
    "AsyncYooMoneyClient",
    # QIWI
    "QiwiClient",
    "AsyncQiwiClient",
    # Tinkoff
    "TinkoffClient",
    "AsyncTinkoffClient",
    # Exceptions
    "RupayError",
    "AuthenticationError",
    "PaymentError",
    "NetworkError",
    "ValidationError",
]
