"""
ЮKassa (YooKassa) клиент
Документация: https://yookassa.ru/developers/api
"""

import requests
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from .exceptions import AuthenticationError, PaymentError, NetworkError, ValidationError


class YuKassaClient:
    """Синхронный клиент для работы с ЮKassa API"""
    
    BASE_URL = "https://api.yookassa.ru/v3"
    
    def __init__(self, shop_id: str, secret_key: str, timeout: int = 30):
        """
        Инициализация клиента ЮKassa
        
        Args:
            shop_id: ID магазина из личного кабинета ЮKassa
            secret_key: Секретный ключ магазина
            timeout: Таймаут запросов в секундах
        """
        if not shop_id:
            raise ValidationError("Shop ID не может быть пустым")
        if not secret_key:
            raise ValidationError("Secret key не может быть пустым")
        
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (shop_id, secret_key)
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Базовый метод для HTTP запросов"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Неверный Shop ID или Secret Key")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('description', f'HTTP {response.status_code}')
                raise PaymentError(f"Ошибка ЮKassa: {error_msg}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        capture: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создать платеж
        
        Args:
            amount: Сумма платежа в рублях
            description: Описание платежа
            return_url: URL для возврата после оплаты
            metadata: Дополнительные данные (до 16 пар ключ-значение)
            capture: Автоматическое подтверждение платежа
            
        Returns:
            Словарь с данными платежа
        """
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        # Генерируем уникальный ключ идемпотентности
        idempotence_key = str(uuid.uuid4())
        
        data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url or "https://example.com/return"
            },
            "capture": capture,
            "description": description[:128]
        }
        
        if metadata:
            data["metadata"] = metadata
        
        headers = {"Idempotence-Key": idempotence_key}
        result = self._request("POST", "payments", json=data, headers=headers)
        
        # Нормализуем ответ для единого интерфейса
        return {
            "id": result.get("id"),
            "confirmation_url": result.get("confirmation", {}).get("confirmation_url"),
            "status": result.get("status"),
            "amount": amount,
            "description": description,
            "paid": result.get("paid", False)
        }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Получить информацию о платеже
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Словарь со статусом платежа
        """
        result = self._request("GET", f"payments/{payment_id}")
        
        # Маппинг статусов для единого интерфейса
        status_map = {
            "pending": "pending",
            "waiting_for_capture": "pending",
            "succeeded": "succeeded",
            "canceled": "canceled"
        }
        
        yukassa_status = result.get("status", "pending")
        
        return {
            "id": payment_id,
            "status": status_map.get(yukassa_status, "pending"),
            "original_status": yukassa_status,
            "amount": float(result.get("amount", {}).get("value", 0)),
            "currency": result.get("amount", {}).get("currency", "RUB"),
            "paid": result.get("paid", False),
            "created_at": result.get("created_at")
        }
    
    def capture_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Подтвердить платеж (для двухстадийной оплаты)
        
        Args:
            payment_id: ID платежа
            amount: Сумма подтверждения (если меньше изначальной)
            
        Returns:
            Результат подтверждения
        """
        idempotence_key = str(uuid.uuid4())
        headers = {"Idempotence-Key": idempotence_key}
        
        data = {}
        if amount:
            data["amount"] = {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            }
        
        return self._request("POST", f"payments/{payment_id}/capture", json=data, headers=headers)
    
    def cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Отменить платеж
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Результат отмены
        """
        idempotence_key = str(uuid.uuid4())
        headers = {"Idempotence-Key": idempotence_key}
        
        return self._request("POST", f"payments/{payment_id}/cancel", headers=headers)
    
    def create_refund(
        self,
        payment_id: str,
        amount: float,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создать возврат платежа
        
        Args:
            payment_id: ID платежа для возврата
            amount: Сумма возврата
            description: Причина возврата
            
        Returns:
            Данные возврата
        """
        if amount <= 0:
            raise ValidationError("Сумма возврата должна быть больше 0")
        
        idempotence_key = str(uuid.uuid4())
        headers = {"Idempotence-Key": idempotence_key}
        
        data = {
            "payment_id": payment_id,
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            }
        }
        
        if description:
            data["description"] = description
        
        return self._request("POST", "refunds", json=data, headers=headers)


class AsyncYuKassaClient:
    """Асинхронный клиент для работы с ЮKassa API"""
    
    BASE_URL = "https://api.yookassa.ru/v3"
    
    def __init__(self, shop_id: str, secret_key: str, timeout: int = 30):
        """
        Инициализация асинхронного клиента ЮKassa
        
        Args:
            shop_id: ID магазина
            secret_key: Секретный ключ
            timeout: Таймаут запросов
        """
        if not shop_id:
            raise ValidationError("Shop ID не может быть пустым")
        if not secret_key:
            raise ValidationError("Secret key не может быть пустым")
        
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.timeout = timeout
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Базовый метод для асинхронных HTTP запросов"""
        import aiohttp
        from aiohttp import BasicAuth
        
        url = f"{self.BASE_URL}/{endpoint}"
        auth = BasicAuth(self.shop_id, self.secret_key)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    auth=auth,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    **kwargs
                ) as response:
                    
                    if response.status == 401:
                        raise AuthenticationError("Неверный Shop ID или Secret Key")
                    elif response.status >= 400:
                        error_data = await response.json() if response.content_length else {}
                        error_msg = error_data.get('description', f'HTTP {response.status}')
                        raise PaymentError(f"Ошибка ЮKassa: {error_msg}")
                    
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    async def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        capture: bool = True
    ) -> Dict[str, Any]:
        """Создать платеж (асинхронно)"""
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        idempotence_key = str(uuid.uuid4())
        
        data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url or "https://example.com/return"
            },
            "capture": capture,
            "description": description[:128]
        }
        
        if metadata:
            data["metadata"] = metadata
        
        headers = {"Idempotence-Key": idempotence_key}
        result = await self._request("POST", "payments", json=data, headers=headers)
        
        return {
            "id": result.get("id"),
            "confirmation_url": result.get("confirmation", {}).get("confirmation_url"),
            "status": result.get("status"),
            "amount": amount,
            "description": description,
            "paid": result.get("paid", False)
        }
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Получить статус платежа (асинхронно)"""
        result = await self._request("GET", f"payments/{payment_id}")
        
        status_map = {
            "pending": "pending",
            "waiting_for_capture": "pending",
            "succeeded": "succeeded",
            "canceled": "canceled"
        }
        
        yukassa_status = result.get("status", "pending")
        
        return {
            "id": payment_id,
            "status": status_map.get(yukassa_status, "pending"),
            "original_status": yukassa_status,
            "amount": float(result.get("amount", {}).get("value", 0)),
            "currency": result.get("amount", {}).get("currency", "RUB"),
            "paid": result.get("paid", False)
        }
