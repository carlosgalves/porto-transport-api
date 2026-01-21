import httpx
from typing import Dict, Any, Optional


class STCPClient:
    BASE_URL = "https://stcp.pt/api"
    
    @staticmethod
    async def fetch_stop_realtime(stop_id: str) -> Optional[Dict[str, Any]]:
        url = f"{STCPClient.BASE_URL}/stops/{stop_id}/realtime"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching real-time data for stop {stop_id}: {e}")
            return None