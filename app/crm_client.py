import httpx
from typing import Any, Dict

from typing import List, Optional
from pydantic import BaseModel, root_validator

class ProductVariant(BaseModel):
    IsDefault: bool = True
    UnitPrice: float = 0
    Title: str
    VariantCode: int
    TitleForInvoice: Optional[str] = None

    @root_validator(pre=True)
    def set_title_invoice(cls, values):
        if "TitleForInvoice" not in values or values["TitleForInvoice"] is None:
            values["TitleForInvoice"] = values.get("Title")
        return values


class ProductData(BaseModel):
    Id: Optional[str] = None
    Code: str
    DidarId: Optional[int] = None
    Title: str
    TitleForInvoice: str
    Unit: str = "دلار"
    UnitPrice: float = 0
    Description: str = ""
    ProductCategoryId: str 
    Variants: List[ProductVariant]

class ContactData(BaseModel):
    Id: Optional[str] = None
    FirstName: str
    LastName: str
    MobilePhone: str
    ProvinceId: str = "c990e86b-a13a-40f4-b21d-79bf09e6e579"
    CityId: str = "00000000-0000-0000-0000-000000000000"
    Fields: Dict[str, Any] = []
    SegmentIds: List[str] = []


class DealItem(BaseModel):
    ProductId: str
    Description: str = ""
    Quantity: int = 1
    UnitPrice: float = 0
    Discount: float = 0
    VariantId: Optional[str] = None


class DealData(BaseModel):
    Id: Optional[str] = None
    PersonId: str
    Title: str
    Price: str = 0
    TaxPercent: int = 9
    PipelineStageId: str
    RegisterDate: str
    Fields: Dict[str, Any] = []

class CardData(BaseModel):
    Id: Optional[str] = None
    DueDate: str
    Priority: int = -2
    PipelineStageId: str
    OwnerId: str
    VisibilityType: str = "OwnerGroup"
    Title: str
    Description: str = ""
    LabelId: str


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
    
    def list_activity_types(self):
        response = self._post("activity/GetActivityType", {})
        return str(response)
    
    def list_custom_field(self):
        response = self._post("customfield/GetCustomFieldList", {})
        return str(response)
    
    def list_pipelines(self):
        response = self._posT("pipeline/list", {})
        return str(response)
    
    def search_contact(self, query: str):
        response = self._post("search/search", {
            "Keyword":query,
            "Types":["contact"]
        })
        return str(response)
    
    def search_company(self, query: str):
        response = self._post("search/search", {
            "Keyword":query,
            "Types":["company"]
        })
        return str(response)
    
    def search_deal(self, query: str):
        response = self._post("search/search", {
            "Keyword":query,
            "Types":["deal"]
        })
        return str(response)
    
    def search_case(self, query: str):
        response = self._post("search/search", {
            "Keyword":query,
            "Types":["case"]
        })
        return str(response)
    
    def search_attachment(self, query: str):
        response = self._post("search/search", {
            "Keyword":query,
            "Types":["attachment"]
        })
        return str(response)
    
    def search_product(self, query: str, num: int = 10):
        response = self._post("product/search", {
            "Criteria":{
                "Keywords":query
            },
            "From":0,
            "Limit":num
        })
        return str(response)
    
    def get_cards(self, owner_id: str, num: int = 10):
        response = self._post("Case/search", {
            "Criteria":{
                "OwnerId": owner_id
            },
            "From":0,
            "Limit":num
        })
        return str(response)
    
    def get_contact_detail(self, id: str):
        response = self._post("contact/GetContactDetail", {
            "Id": id
        })
        return str(response)
    
    def get_deal_detail(self, id: str):
        response = self._post("contact/setstatus", {
            "Id": id
        })
        return str(response)
    

    def save_product(self, product_data: ProductData):
        response = self._post("product/save", {
            "Product": product_data.dict()
        })
        return str(response)
    
    def save_contact(self, contact_data: ContactData):
        response = self._post("contact/save", {
            "Contact": contact_data.dict()
        })
        return str(response)
    
    def save_deal(self, deal: DealData, deal_items: List[DealItem]):
        response = self._post("deal/save", {
            "Deal": deal.dict(),
            "DealItems": [item.dict() for item in deal_items]
        })
        return str(response)

    def save_card(self, card_data: CardData):
        response = self._post("case/save", {
            "Case": card_data.dict()
        })
        return str(response)

    def change_deal_status(self, id: str, status: str):
        response = self._post("deal/setstatus", {
            "Id": id,
            "Status": status
        })
        return str(response)