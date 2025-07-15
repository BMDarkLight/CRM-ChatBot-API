import httpx
from typing import Any, Dict

class CRMClient:
    def __init__(self, api_key: str, base_url: str = "https://app.didar.me/api"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.Client(timeout=10.0)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path}?apikey={self.api_key}"

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.post(self._url(path), json=payload)
        response.raise_for_status()
        return response.json()["Response"]
    
    def _get(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.get(self._url(path), params=payload)
        response.raise_for_status()
        return response.json()["Response"]
    
    def _delete(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.delete(self._url(path), json=payload)
        response.raise_for_status()
        return response.json()["Response"]
    
    def list_users(self):
        response = self._post("User/List", {})
        return str(response)
    
    def list_product_categories(self):
        response = self._post("product/categories", {})
        return str(response)
    
    def list_products(self):
        response = self._post("product/GetProductsList", {})
        return str(response)