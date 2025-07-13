import httpx

class CRMClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"app.didar.me/api/contact/save?apikey={self.api_key}"
        
    