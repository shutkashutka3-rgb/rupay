"""
ЮMoney (бывший Яндекс.Деньги) клиент
Документация: https://yoomoney.ru/docs/
"""

import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from .exceptions import AuthenticationError, PaymentError, NetworkError, ValidationError


class YooMoneyClient:
    """Синхронный клиент для работы с ЮMoney API"""
    
    BASE_URL = "https://yoomoney.ru/api"
    
    def __init__(self, token: str, timeout: int = 30):
        """
        Инициализация клиента ЮMoney
        
        Args:
            token: OAuth токен приложения
            timeout: Таймаут запросов в секундах
        """
        if not token:
            raise ValidationError("Токен не может быть пустым")
        
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Базовый метод для HTTP запросов"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Неверный токен ЮMoney")
            
            result = response.json()
            
            if "error" in result:
                raise PaymentError(f"Ошибка ЮMoney: {result.get('error')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Получить информацию об аккаунте
        
        Returns:
            Словарь с информацией об аккаунте (номер счета, баланс, тип аккаунта)
        """
        return self._request("POST", "account-info")
    
    def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        label: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создать новый платеж
        
        Args:
            amount: Сумма платежа
            description: Описание платежа
            return_url: URL для возврата после оплаты
            label: Метка платежа для идентификации
            
        Returns:
            Словарь с данными платежа включая confirmation_url для оплаты
        """
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        data = {
            "amount": str(amount),
            "description": description[:128],  # Максимум 128 символов
        }
        
        if return_url:
            data["return_url"] = return_url
        if label:
            data["label"] = label
            
        # Для упрощения возвращаем структуру с confirmation_url
        # В реальном API ЮMoney используется метод request-payment
        payment_data = self._request("POST", "request-payment", data)
        
        # Добавляем ссылку для оплаты
        request_id = payment_data.get("request_id", "")
        payment_data["confirmation_url"] = f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={request_id}"
        payment_data["id"] = request_id
        
        return payment_data
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверить статус платежа
        
        Args:
            payment_id: ID платежа
            
        Returns:
            Словарь со статусом платежа
        """
        data = {"request_id": payment_id}
        result = self._request("POST", "process-payment", data)
        
        # Нормализуем статус
        status_map = {
            "success": "succeeded",
            "refused": "canceled",
            "in_progress": "pending"
        }
        
        status = result.get("status", "pending")
        result["status"] = status_map.get(status, status)
        
        return result
    
    def get_operation_history(
        self,
        type: Optional[str] = None,
        label: Optional[str] = None,
        from_date: Optional[datetime] = None,
        till_date: Optional[datetime] = None,
        records: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Получить историю операций
        
        Args:
            type: Тип операций (deposition/payment)
            label: Фильтр по метке
            from_date: Начальная дата
            till_date: Конечная дата
            records: Количество записей (макс. 100)
            
        Returns:
            Список операций
        """
        data = {"records": min(records, 100)}
        
        if type:
            data["type"] = type
        if label:
            data["label"] = label
        if from_date:
            data["from"] = from_date.isoformat()
        if till_date:
            data["till"] = till_date.isoformat()
        
        result = self._request("POST", "operation-history", data)
        return result.get("operations", [])
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Получить текущий баланс
        
        Returns:
            Словарь с балансом и валютой
        """
        info = self.get_account_info()
        return {
            "amount": float(info.get("balance", 0)),
            "currency": info.get("currency", "RUB")
        }


class AsyncYooMoneyClient:
    """Асинхронный клиент для работы с ЮMoney API"""
    
    BASE_URL = "https://yoomoney.ru/api"
    
    def __init__(self, token: str, timeout: int = 30):
        """
        Инициализация асинхронного клиента ЮMoney
        
        Args:
            token: OAuth токен приложения
            timeout: Таймаут запросов в секундах
        """
        if not token:
            raise ValidationError("Токен не может быть пустым")
        
        self.token = token
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Базовый метод для асинхронных HTTP запросов"""
        import aiohttp
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 401:
                        raise AuthenticationError("Неверный токен ЮMoney")
                    
                    result = await response.json()
                    
                    if "error" in result:
                        raise PaymentError(f"Ошибка ЮMoney: {result.get('error')}")
                    
                    return result
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Получить информацию об аккаунте"""
        return await self._request("POST", "account-info")
    
    async def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создать новый платеж (асинхронно)"""
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        data = {
            "amount": str(amount),
            "description": description[:128],
        }
        
        if return_url:
            data["return_url"] = return_url
        if label:
            data["label"] = label
        
        payment_data = await self._request("POST", "request-payment", data)
        
        request_id = payment_data.get("request_id", "")
        payment_data["confirmation_url"] = f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={request_id}"
        payment_data["id"] = request_id
        
        return payment_data
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверить статус платежа (асинхронно)"""
        data = {"request_id": payment_id}
        result = await self._request("POST", "process-payment", data)
        
        status_map = {
            "success": "succeeded",
            "refused": "canceled",
            "in_progress": "pending"
        }
        
        status = result.get("status", "pending")
        result["status"] = status_map.get(status, status)
        
        return result
    
    async def get_balance(self) -> Dict[str, Any]:
        """Получить текущий баланс (асинхронно)"""
        info = await self.get_account_info()
        return {
            "amount": float(info.get("balance", 0)),
            "currency": info.get("currency", "RUB")
        }
