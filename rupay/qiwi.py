"""
QIWI Wallet клиент
Документация: https://developer.qiwi.com/
"""

import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from .exceptions import AuthenticationError, PaymentError, NetworkError, ValidationError


class QiwiClient:
    """Синхронный клиент для работы с QIWI Wallet API"""
    
    BASE_URL = "https://edge.qiwi.com"
    
    def __init__(self, token: str, phone: str, timeout: int = 30):
        """
        Инициализация клиента QIWI
        
        Args:
            token: API токен (из настроек QIWI кошелька)
            phone: Номер телефона кошелька (например: +79001234567)
            timeout: Таймаут запросов в секундах
        """
        if not token:
            raise ValidationError("Токен не может быть пустым")
        if not phone:
            raise ValidationError("Номер телефона не может быть пустым")
        
        self.token = token
        self.phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
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
                raise AuthenticationError("Неверный токен QIWI")
            elif response.status_code == 403:
                raise AuthenticationError("Доступ запрещен. Проверьте права токена")
            elif response.status_code >= 400:
                raise PaymentError(f"Ошибка QIWI API: {response.status_code} - {response.text}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Получить баланс кошелька
        
        Returns:
            Словарь с балансом и валютой
        """
        endpoint = f"funding-sources/v2/persons/{self.phone}/accounts"
        result = self._request("GET", endpoint)
        
        # Берем баланс в рублях (код 643)
        for account in result.get("accounts", []):
            if account.get("currency") == 643:  # RUB
                return {
                    "amount": float(account.get("balance", {}).get("amount", 0)),
                    "currency": "RUB"
                }
        
        return {"amount": 0.0, "currency": "RUB"}
    
    def get_history(
        self,
        rows: int = 10,
        operation: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Получить историю платежей
        
        Args:
            rows: Количество записей (макс. 50)
            operation: Тип операций (IN/OUT/ALL)
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            Список транзакций
        """
        endpoint = f"payment-history/v2/persons/{self.phone}/payments"
        
        params = {
            "rows": min(rows, 50)
        }
        
        if operation:
            params["operation"] = operation
        if start_date:
            params["startDate"] = start_date.strftime("%Y-%m-%dT%H:%M:%S+03:00")
        if end_date:
            params["endDate"] = end_date.strftime("%Y-%m-%dT%H:%M:%S+03:00")
        
        result = self._request("GET", endpoint, params=params)
        
        # Нормализуем формат транзакций
        transactions = []
        for item in result.get("data", []):
            transactions.append({
                "id": item.get("txnId"),
                "date": item.get("date"),
                "sum": float(item.get("sum", {}).get("amount", 0)),
                "currency": "RUB",
                "status": item.get("status"),
                "comment": item.get("comment", ""),
                "type": item.get("type")
            })
        
        return transactions
    
    def send_payment(
        self,
        amount: float,
        recipient: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отправить платеж на другой QIWI кошелек
        
        Args:
            amount: Сумма перевода
            recipient: Номер получателя
            comment: Комментарий к платежу
            
        Returns:
            Словарь с результатом платежа
        """
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        endpoint = f"sinap/api/v2/terms/99/payments"
        
        recipient_clean = recipient.replace("+", "").replace(" ", "").replace("-", "")
        
        data = {
            "id": str(int(datetime.now().timestamp() * 1000)),
            "sum": {
                "amount": amount,
                "currency": "643"
            },
            "paymentMethod": {
                "type": "Account",
                "accountId": "643"
            },
            "fields": {
                "account": recipient_clean
            }
        }
        
        if comment:
            data["comment"] = comment[:255]
        
        result = self._request("POST", endpoint, json=data)
        
        return {
            "id": result.get("transaction", {}).get("id"),
            "status": result.get("transaction", {}).get("state", {}).get("code"),
            "amount": amount,
            "recipient": recipient
        }
    
    def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Создать платеж (для совместимости с единым интерфейсом)
        Для QIWI это создает ссылку на форму оплаты
        
        Args:
            amount: Сумма платежа
            description: Описание
            return_url: URL возврата
            
        Returns:
            Словарь с данными платежа
        """
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        # Генерируем ID счета
        bill_id = f"order-{int(datetime.now().timestamp())}"
        
        # Формируем ссылку на оплату (QIWI P2P)
        payment_url = (
            f"https://oplata.qiwi.com/create?"
            f"publicKey=YOUR_PUBLIC_KEY&"
            f"billId={bill_id}&"
            f"amount={amount}&"
            f"comment={description[:255]}"
        )
        
        if return_url:
            payment_url += f"&successUrl={return_url}"
        
        return {
            "id": bill_id,
            "confirmation_url": payment_url,
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
        # Для QIWI проверяем по истории
        history = self.get_history(rows=50)
        
        for transaction in history:
            if str(transaction.get("id")) == str(payment_id):
                status_map = {
                    "SUCCESS": "succeeded",
                    "ERROR": "canceled",
                    "WAITING": "pending"
                }
                
                return {
                    "id": payment_id,
                    "status": status_map.get(transaction.get("status", ""), "pending"),
                    "amount": transaction.get("sum"),
                    "currency": transaction.get("currency")
                }
        
        return {
            "id": payment_id,
            "status": "not_found"
        }


class AsyncQiwiClient:
    """Асинхронный клиент для работы с QIWI Wallet API"""
    
    BASE_URL = "https://edge.qiwi.com"
    
    def __init__(self, token: str, phone: str, timeout: int = 30):
        """
        Инициализация асинхронного клиента QIWI
        
        Args:
            token: API токен
            phone: Номер телефона кошелька
            timeout: Таймаут запросов
        """
        if not token:
            raise ValidationError("Токен не может быть пустым")
        if not phone:
            raise ValidationError("Номер телефона не может быть пустым")
        
        self.token = token
        self.phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Базовый метод для асинхронных HTTP запросов"""
        import aiohttp
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    **kwargs
                ) as response:
                    
                    if response.status == 401:
                        raise AuthenticationError("Неверный токен QIWI")
                    elif response.status == 403:
                        raise AuthenticationError("Доступ запрещен")
                    elif response.status >= 400:
                        text = await response.text()
                        raise PaymentError(f"Ошибка QIWI API: {response.status} - {text}")
                    
                    return await response.json()
                    
        except aiohttp.ClientError as e:
            raise NetworkError(f"Ошибка сети: {str(e)}")
    
    async def get_balance(self) -> Dict[str, Any]:
        """Получить баланс кошелька (асинхронно)"""
        endpoint = f"funding-sources/v2/persons/{self.phone}/accounts"
        result = await self._request("GET", endpoint)
        
        for account in result.get("accounts", []):
            if account.get("currency") == 643:
                return {
                    "amount": float(account.get("balance", {}).get("amount", 0)),
                    "currency": "RUB"
                }
        
        return {"amount": 0.0, "currency": "RUB"}
    
    async def get_history(self, rows: int = 10) -> List[Dict[str, Any]]:
        """Получить историю платежей (асинхронно)"""
        endpoint = f"payment-history/v2/persons/{self.phone}/payments"
        params = {"rows": min(rows, 50)}
        
        result = await self._request("GET", endpoint, params=params)
        
        transactions = []
        for item in result.get("data", []):
            transactions.append({
                "id": item.get("txnId"),
                "date": item.get("date"),
                "sum": float(item.get("sum", {}).get("amount", 0)),
                "currency": "RUB",
                "status": item.get("status"),
                "comment": item.get("comment", "")
            })
        
        return transactions
    
    async def create_payment(
        self,
        amount: float,
        description: str,
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создать платеж (асинхронно)"""
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0")
        
        bill_id = f"order-{int(datetime.now().timestamp())}"
        
        payment_url = (
            f"https://oplata.qiwi.com/create?"
            f"publicKey=YOUR_PUBLIC_KEY&"
            f"billId={bill_id}&"
            f"amount={amount}&"
            f"comment={description[:255]}"
        )
        
        if return_url:
            payment_url += f"&successUrl={return_url}"
        
        return {
            "id": bill_id,
            "confirmation_url": payment_url,
            "amount": amount,
            "description": description,
            "status": "pending"
        }
