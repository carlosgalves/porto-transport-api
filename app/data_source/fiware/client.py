import httpx
from typing import List, Dict, Any
from app.core.config import settings


class FIWAREClient:

    BASE_URL = "https://broker.fiware.urbanplatform.portodigital.pt/v2"
    
    @staticmethod
    async def fetch_vehicles(limit: int = 1000) -> List[Dict[str, Any]]:
        url = f"{FIWAREClient.BASE_URL}/entities"
        params = {
            "q": "vehicleType==bus",
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()