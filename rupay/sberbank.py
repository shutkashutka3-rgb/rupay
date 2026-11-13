"""
СберБанк Acquiring клиент
Документация: https://securepayments.sberbank.ru/wiki/doku.php/
"""

import requests
from typing import Dict, Any, Optional
from datetime import datetime
from .exceptions import AuthenticationError, PaymentError, NetworkError, ValidationError


class SberbankClient:
    """Синхронный клиент для работы с СберБанк Acquiring API"""
    
    BASE_URL = "https://securepayments.sberbank.ru/payment/rest"
    
    def __init__(self, username: str, password: str, timeout: int = 30):
        """
        Инициализация клиента СберБанк
        
        Args:
            username: Логин продавца из личного кабинета
            password: Пароль продавца
            timeout: Таймаут запросов в секундах
        """
        if not username:
            raise ValidationError("Username не может быть пустым")
        if not password:
            raise ValidationError("Password не может быть пустым")
        
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
    
    def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Базовый метод для HTTP запросов"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Добавляем учетные данные
        params.update({
            "userName": self.username,
            "password": self.password
        })
        
        try:
            response = self.session.post(
                url=url,
                params=params,
                timeout=self.timeout
            )
            
            result = response.json()
            
            # Проверка на ошибки
            if "errorCode" in result and result["errorCode"] != "0":
                error_code = result.get("errorCode")
                error_msg = result.get("errorMessage", "Неизвестная ошибка")
                
                if error_code == "5":
                    raise AuthenticationError(f"Ошибка авторизации: {error_msg}")
                else:
                    raise PaymentError(f"Ошибка СберБанк [{error_code}]: {error_msg}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    def register_order(
        self,
        order_number: str,
        amount: int,
        return_url: str,
        description: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Регистрация заказа (создание платежа)
        
        Args:
            order_number: Уникальный номер заказа
            amount: Сумма в копейках (например, 10000 = 100.00 руб)
            return_url: URL для возврата после оплаты
            description: Описание заказа
            
        Returns:
            Словарь с данными заказа
        """
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        if not order_number:
            raise ValidationError("Номер заказа не может быть пустым")
        if not return_url:
            raise ValidationError("Return URL не может быть пустым")
        
        params = {
            "orderNumber": order_number,
            "amount": amount,
            "returnUrl": return_url
        }
        
        if description:
            params["description"] = description[:512]
        
        # Добавляем дополнительные параметры
        params.update(kwargs)
        
        result = self._request("register.do", params)
        
        return {
            "order_id": result.get("orderId"),
            "form_url": result.get("formUrl"),
            "confirmation_url": result.get("formUrl"),  # Для единого интерфейса
            "order_number": order_number,
            "amount": amount / 100,  # Конвертируем обратно в рубли
            "status": "pending"
        }
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Получить статус заказа
        
        Args:
            order_id: ID заказа (из register_order)
            
        Returns:
            Словарь со статусом заказа
        """
        params = {"orderId": order_id}
        result = self._request("getOrderStatusExtended.do", params)
        
        # Маппинг статусов СберБанк
        # 0 - Заказ зарегистрирован, но не оплачен
        # 1 - Предавторизованная сумма захолдирована
        # 2 - Проведена полная авторизация суммы заказа
        # 3 - Авторизация отменена
        # 4 - По транзакции была проведена операция возврата
        # 5 - Инициирована авторизация через ACS банка-эмитента
        # 6 - Авторизация отклонена
        
        status_map = {
            0: "pending",
            1: "pending",
            2: "succeeded",
            3: "canceled",
            4: "refunded",
            5: "pending",
            6: "canceled"
        }
        
        sber_status = result.get("orderStatus", 0)
        
        return {
            "id": order_id,
            "status": status_map.get(sber_status, "pending"),
            "original_status": sber_status,
            "amount": result.get("amount", 0) / 100,
            "currency": "RUB",
            "order_number": result.get("orderNumber"),
            "error_code": result.get("errorCode"),
            "error_message": result.get("errorMessage")
        }
    
    def reverse_order(self, order_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """
        Отменить заказ (возврат средств)
        
        Args:
            order_id: ID заказа
            amount: Сумма возврата в копейках (если частичный возврат)
            
        Returns:
            Результат отмены
        """
        params = {"orderId": order_id}
        
        if amount:
            params["amount"] = amount
        
        return self._request("reverse.do", params)
    
    def refund_order(self, order_id: str, amount: int) -> Dict[str, Any]:
        """
        Возврат средств по заказу
        
        Args:
            order_id: ID заказа
            amount: Сумма возврата в копейках
            
        Returns:
            Результат возврата
        """
        if amount <= 0:
            raise ValidationError("Сумма возврата должна быть больше 0")
        
        params = {
            "orderId": order_id,
            "amount": amount
        }
        
        return self._request("refund.do", params)
    
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
            return_url: URL возврата
            
        Returns:
            Словарь с данными платежа
        """
        # Конвертируем рубли в копейки
        amount_kopecks = int(amount * 100)
        
        # Генерируем уникальный номер заказа
        order_number = f"order-{int(datetime.now().timestamp())}"
        
        result = self.register_order(
            order_number=order_number,
            amount=amount_kopecks,
            return_url=return_url or "https://example.com/return",
            description=description,
            **kwargs
        )
        
        return {
            "id": result["order_id"],
            "confirmation_url": result["form_url"],
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
        return self.get_order_status(payment_id)


class AsyncSberbankClient:
    """Асинхронный клиент для работы с СберБанк Acquiring API"""
    
    BASE_URL = "https://securepayments.sberbank.ru/payment/rest"
    
    def __init__(self, username: str, password: str, timeout: int = 30):
        """
        Инициализация асинхронного клиента СберБанк
        
        Args:
            username: Логин продавца
            password: Пароль продавца
            timeout: Таймаут запросов
        """
        if not username:
            raise ValidationError("Username не может быть пустым")
        if not password:
            raise ValidationError("Password не может быть пустым")
        
        self.username = username
        self.password = password
        self.timeout = timeout
    
    async def _request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Базовый метод для асинхронных HTTP запросов"""
        import aiohttp
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        params.update({
            "userName": self.username,
            "password": self.password
        })
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    result = await response.json()
                    
                    if "errorCode" in result and result["errorCode"] != "0":
                        error_code = result.get("errorCode")
                        error_msg = result.get("errorMessage", "Неизвестная ошибка")
                        
                        if error_code == "5":
                            raise AuthenticationError(f"Ошибка авторизации: {error_msg}")
                        else:
                            raise PaymentError(f"Ошибка СберБанк [{error_code}]: {error_msg}")
                    
                    return result
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    async def register_order(
        self,
        order_number: str,
        amount: int,
        return_url: str,
        description: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Регистрация заказа (асинхронно)"""
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        params = {
            "orderNumber": order_number,
            "amount": amount,
            "returnUrl": return_url
        }
        
        if description:
            params["description"] = description[:512]
        
        params.update(kwargs)
        
        result = await self._request("register.do", params)
        
        return {
            "order_id": result.get("orderId"),
            "form_url": result.get("formUrl"),
            "confirmation_url": result.get("formUrl"),
            "order_number": order_number,
            "amount": amount / 100,
            "status": "pending"
        }
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Получить статус заказа (асинхронно)"""
        params = {"orderId": order_id}
        result = await self._request("getOrderStatusExtended.do", params)
        
        status_map = {
            0: "pending",
            1: "pending",
            2: "succeeded",
            3: "canceled",
            4: "refunded",
            5: "pending",
            6: "canceled"
        }
        
        sber_status = result.get("orderStatus", 0)
        
        return {
            "id": order_id,
            "status": status_map.get(sber_status, "pending"),
            "original_status": sber_status,
            "amount": result.get("amount", 0) / 100,
            "currency": "RUB",
            "order_number": result.get("orderNumber")
        }
    
    async def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Создать платеж (асинхронно)"""
        amount_kopecks = int(amount * 100)
        order_number = f"order-{int(datetime.now().timestamp())}"
        
        result = await self.register_order(
            order_number=order_number,
            amount=amount_kopecks,
            return_url=return_url or "https://example.com/return",
            description=description,
            **kwargs
        )
        
        return {
            "id": result["order_id"],
            "confirmation_url": result["form_url"],
            "amount": amount,
            "description": description,
            "status": "pending"
        }
