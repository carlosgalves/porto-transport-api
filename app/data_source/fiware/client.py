import httpx
from typing import List, Dict, Any

from app.data_source.fiware.parser import FIWAREParser


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

    @staticmethod
    async def fetch_vehicle_ids_by_nr_viagem(limit: int = 1000) -> Dict[str, str]:
        vehicles_data = await FIWAREClient.fetch_vehicles(limit=limit)
        return FIWAREParser.build_nr_viagem_to_vehicle_id(vehicles_data)