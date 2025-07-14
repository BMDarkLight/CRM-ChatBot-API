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
        return response.json()

    def save_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("contact/save", {"Contact": contact})

    def search_contacts(self, criteria: Dict[str, Any], from_: int = 0, limit: int = 30) -> Dict[str, Any]:
        return self._post("contact/search", {"Criteria": criteria, "From": from_, "Limit": limit})

    def save_company(self, company: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("company/save", {"Company": company})

    def search_companies(self, criteria: Dict[str, Any], from_: int = 0, limit: int = 30) -> Dict[str, Any]:
        return self._post("company/search", {"Criteria": criteria, "From": from_, "Limit": limit})

    def save_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("activity/save", {"Activity": activity})

    def search_activities(self, criteria: Dict[str, Any], from_: int = 0, limit: int = 30) -> Dict[str, Any]:
        return self._post("activity/search", {"Criteria": criteria, "From": from_, "Limit": limit})

    def save_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("product/save", {"Product": product})

    def list_products(self, from_: int = 0, limit: int = 30) -> Dict[str, Any]:
        return self._post("product/list", {"From": from_, "Limit": limit})

    def search_products(self, criteria: Dict[str, Any], from_: int = 0, limit: int = 30) -> Dict[str, Any]:
        return self._post("product/search", {"Criteria": criteria, "From": from_, "Limit": limit})

    def save_deal(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("deal/save", {"Deal": deal})

    def search_deals(self, criteria: Dict[str, Any], from_: int = 0, limit: int = 30) -> Dict[str, Any]:
        return self._post("deal/search", {"Criteria": criteria, "From": from_, "Limit": limit})

    def change_deal_status(self, deal_id: str, status_id: str) -> Dict[str, Any]:
        return self._post("deal/changeStatus", {"DealId": deal_id, "StatusId": status_id})

    def list_users(self) -> Dict[str, Any]:
        return self._post("user/list", {})

    def save_note(self, note: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("note/save", {"Note": note})

    def list_custom_fields(self) -> Dict[str, Any]:
        return self._post("customfields/list", {})

    def list_pipelines(self) -> Dict[str, Any]:
        return self._post("deal/pipeline/list", {})

    def list_cards(self) -> Dict[str, Any]:
        return self._post("card/pipeline/list", {})