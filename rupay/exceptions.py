"""
Базовые исключения для rupay
"""


class RupayError(Exception):
    """Базовое исключение для всех ошибок rupay"""
    pass


class AuthenticationError(RupayError):
    """Ошибка аутентификации (неверный токен/ключ)"""
    pass


class PaymentError(RupayError):
    """Ошибка при создании или обработке платежа"""
    pass


class NetworkError(RupayError):
    """Ошибка сети или соединения"""
    pass


class ValidationError(RupayError):
    """Ошибка валидации входных данных"""
    pass
