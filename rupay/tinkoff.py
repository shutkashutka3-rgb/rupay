"""
Tinkoff Acquiring клиент
Документация: https://www.tinkoff.ru/kassa/develop/api/
"""

import requests
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from .exceptions import AuthenticationError, PaymentError, NetworkError, ValidationError


class TinkoffClient:
    """Синхронный клиент для работы с Tinkoff Acquiring API"""
    
    BASE_URL = "https://securepay.tinkoff.ru/v2"
    
    def __init__(self, terminal_key: str, secret_key: str, timeout: int = 30):
        """
        Инициализация клиента Tinkoff
        
        Args:
            terminal_key: Ключ терминала (из личного кабинета)
            secret_key: Секретный ключ для подписи запросов
            timeout: Таймаут запросов в секундах
        """
        if not terminal_key:
            raise ValidationError("Terminal key не может быть пустым")
        if not secret_key:
            raise ValidationError("Secret key не может быть пустым")
        
        self.terminal_key = terminal_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _generate_token(self, data: Dict[str, Any]) -> str:
        """
        Генерация токена для подписи запроса
        
        Args:
            data: Данные запроса
            
        Returns:
            SHA-256 хеш для подписи
        """
        # Добавляем секретный ключ и сортируем параметры
        token_data = {**data, "Password": self.secret_key}
        
        # Исключаем специальные поля
        excluded = ["Token", "Receipt", "DATA", "Shops"]
        sorted_values = [str(token_data[key]) for key in sorted(token_data.keys()) if key not in excluded]
        
        # Генерируем SHA-256
        token_string = "".join(sorted_values)
        return hashlib.sha256(token_string.encode()).hexdigest()
    
    def _request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Базовый метод для HTTP запросов"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Добавляем терминал и токен
        data["TerminalKey"] = self.terminal_key
        data["Token"] = self._generate_token(data)
        
        try:
            response = self.session.post(
                url=url,
                json=data,
                timeout=self.timeout
            )
            
            result = response.json()
            
            # Проверка на ошибки
            if not result.get("Success", False):
                error_code = result.get("ErrorCode", "UNKNOWN")
                error_message = result.get("Message", "Неизвестная ошибка")
                
                if error_code == "UNAUTHORIZED":
                    raise AuthenticationError(f"Ошибка авторизации: {error_message}")
                else:
                    raise PaymentError(f"Ошибка Tinkoff [{error_code}]: {error_message}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    def init_payment(
        self,
        amount: int,
        order_id: str,
        description: str,
        customer_key: Optional[str] = None,
        receipt: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Инициализация платежа
        
        Args:
            amount: Сумма в копейках (например, 10000 = 100.00 руб)
            order_id: Уникальный идентификатор заказа
            description: Описание платежа
            customer_key: Идентификатор покупателя (для сохранения карты)
            receipt: Данные чека для 54-ФЗ
            
        Returns:
            Словарь с данными платежа включая PaymentURL
        """
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        if not order_id:
            raise ValidationError("Order ID не может быть пустым")
        
        data = {
            "Amount": amount,
            "OrderId": order_id,
            "Description": description[:250]
        }
        
        if customer_key:
            data["CustomerKey"] = customer_key
        if receipt:
            data["Receipt"] = receipt
        
        # Добавляем дополнительные параметры
        data.update(kwargs)
        
        result = self._request("Init", data)
        
        return {
            "PaymentId": result.get("PaymentId"),
            "PaymentURL": result.get("PaymentURL"),
            "Status": result.get("Status"),
            "OrderId": order_id,
            "Amount": amount
        }
    
    def get_state(self, payment_id: str) -> Dict[str, Any]:
        """
        Получить статус платежа
        
        Args:
            payment_id: ID платежа из init_payment
            
        Returns:
            Словарь со статусом платежа
        """
        data = {
            "PaymentId": payment_id
        }
        
        result = self._request("GetState", data)
        
        # Маппинг статусов для единого интерфейса
        status_map = {
            "NEW": "pending",
            "FORM_SHOWED": "pending",
            "AUTHORIZING": "pending",
            "3DS_CHECKING": "pending",
            "3DS_CHECKED": "pending",
            "AUTHORIZED": "pending",
            "CONFIRMED": "succeeded",
            "PARTIAL_REFUNDED": "succeeded",
            "REJECTED": "canceled",
            "REFUNDED": "refunded",
            "CANCELED": "canceled"
        }
        
        tinkoff_status = result.get("Status", "NEW")
        
        return {
            "PaymentId": payment_id,
            "Status": status_map.get(tinkoff_status, "pending"),
            "OriginalStatus": tinkoff_status,
            "Amount": result.get("Amount"),
            "OrderId": result.get("OrderId")
        }
    
    def confirm_payment(self, payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Подтвердить платеж (для двухстадийной оплаты)
        
        Args:
            payment_id: ID платежа
            amount: Сумма подтверждения (если меньше изначальной)
            
        Returns:
            Результат подтверждения
        """
        data = {
            "PaymentId": payment_id
        }
        
        if amount:
            data["Amount"] = amount
        
        return self._request("Confirm", data)
    
    def cancel_payment(self, payment_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Отменить платеж
        
        Args:
            payment_id: ID платежа
            amount: Сумма для частичной отмены
            
        Returns:
            Результат отмены
        """
        data = {
            "PaymentId": payment_id
        }
        
        if amount:
            data["Amount"] = amount
        
        return self._request("Cancel", data)
    
    def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создать платеж (для совместимости с единым интерфейсом)
        
        Args:
            amount: Сумма в рублях
            description: Описание
            return_url: URL возврата (не используется в Tinkoff)
            
        Returns:
            Словарь с данными платежа
        """
        # Конвертируем рубли в копейки
        amount_kopecks = int(amount * 100)
        
        # Генерируем уникальный Order ID
        order_id = f"order-{int(datetime.now().timestamp())}"
        
        result = self.init_payment(
            amount=amount_kopecks,
            order_id=order_id,
            description=description,
            **kwargs
        )
        
        return {
            "id": result["PaymentId"],
            "confirmation_url": result["PaymentURL"],
            "amount": amount,
            "description": description,
            "status": "pending"
        }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверить статус платежа (для совместимости с единым интерфейсом)
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Словарь со статусом
        """
        state = self.get_state(payment_id)
        
        return {
            "id": payment_id,
            "status": state["Status"],
            "amount": state["Amount"] / 100 if state.get("Amount") else 0,
            "currency": "RUB"
        }


class AsyncTinkoffClient:
    """Асинхронный клиент для работы с Tinkoff Acquiring API"""
    
    BASE_URL = "https://securepay.tinkoff.ru/v2"
    
    def __init__(self, terminal_key: str, secret_key: str, timeout: int = 30):
        """
        Инициализация асинхронного клиента Tinkoff
        
        Args:
            terminal_key: Ключ терминала
            secret_key: Секретный ключ
            timeout: Таймаут запросов
        """
        if not terminal_key:
            raise ValidationError("Terminal key не может быть пустым")
        if not secret_key:
            raise ValidationError("Secret key не может быть пустым")
        
        self.terminal_key = terminal_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def _generate_token(self, data: Dict[str, Any]) -> str:
        """Генерация токена для подписи"""
        token_data = {**data, "Password": self.secret_key}
        excluded = ["Token", "Receipt", "DATA", "Shops"]
        sorted_values = [str(token_data[key]) for key in sorted(token_data.keys()) if key not in excluded]
        token_string = "".join(sorted_values)
        return hashlib.sha256(token_string.encode()).hexdigest()
    
    async def _request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Базовый метод для асинхронных HTTP запросов"""
        import aiohttp
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        data["TerminalKey"] = self.terminal_key
        data["Token"] = self._generate_token(data)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=url,
                    json=data,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    result = await response.json()
                    
                    if not result.get("Success", False):
                        error_code = result.get("ErrorCode", "UNKNOWN")
                        error_message = result.get("Message", "Неизвестная ошибка")
                        
                        if error_code == "UNAUTHORIZED":
                            raise AuthenticationError(f"Ошибка авторизации: {error_message}")
                        else:
                            raise PaymentError(f"Ошибка Tinkoff [{error_code}]: {error_message}")
                    
                    return result
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    async def init_payment(
        self,
        amount: int,
        order_id: str,
        description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Инициализация платежа (асинхронно)"""
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        data = {
            "Amount": amount,
            "OrderId": order_id,
            "Description": description[:250]
        }
        data.update(kwargs)
        
        result = await self._request("Init", data)
        
        return {
            "PaymentId": result.get("PaymentId"),
            "PaymentURL": result.get("PaymentURL"),
            "Status": result.get("Status"),
            "OrderId": order_id,
            "Amount": amount
        }
    
    async def get_state(self, payment_id: str) -> Dict[str, Any]:
        """Получить статус платежа (асинхронно)"""
        data = {"PaymentId": payment_id}
        result = await self._request("GetState", data)
        
        status_map = {
            "NEW": "pending",
            "CONFIRMED": "succeeded",
            "REJECTED": "canceled",
            "REFUNDED": "refunded",
            "CANCELED": "canceled"
        }
        
        tinkoff_status = result.get("Status", "NEW")
        
        return {
            "PaymentId": payment_id,
            "Status": status_map.get(tinkoff_status, "pending"),
            "OriginalStatus": tinkoff_status,
            "Amount": result.get("Amount"),
            "OrderId": result.get("OrderId")
        }
    
    async def create_payment(
        self,
        amount: float,
        description: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Создать платеж (асинхронно)"""
        amount_kopecks = int(amount * 100)
        order_id = f"order-{int(datetime.now().timestamp())}"
        
        result = await self.init_payment(
            amount=amount_kopecks,
            order_id=order_id,
            description=description,
            **kwargs
        )
        
        return {
            "id": result["PaymentId"],
            "confirmation_url": result["PaymentURL"],
            "amount": amount,
            "description": description,
            "status": "pending"
        }
