from typing import List, Dict, Any, Optional
from datetime import datetime, time


class STCPParser:
    SERVICE_TYPE_MAP = {1: "U", 2: "S", 3: "D"}
    
    @staticmethod
    def parse_trip_id(trip_id: str) -> Dict[str, Any]:
        """
        Parse trip_id to extract route_id, direction_id, service_id.
        
        Format: "600_0_2|194|D1|T13|N6"
        - "600_0_2": route_id="600", direction_id_raw="2" (third value)
          - If direction_id_raw == "1", then direction_id = 0
          - If direction_id_raw == "2", then direction_id = 1
        - "D1": service_type = 1 -> service_id = "U"
        - "D2": service_type = 2 -> service_id = "S"
        - "D3": service_type = 3 -> service_id = "D"
        
        Note: trip_number is not currently provided by STCP Realtime Bus Data
        """
        parts = trip_id.split("|")
        if not parts:
            raise ValueError(f"Invalid trip_id format: {trip_id}")
        
        # example: "600_0_2" -> ["600", "0", "2"]
        first_part = parts[0]
        first_parts = first_part.split("_")
        if len(first_parts) < 3:
            raise ValueError(f"Invalid trip_id format: {trip_id}")
        
        route_id = first_parts[0]
        direction_id_raw = first_parts[2]
        
        # Map direction_id: 1 -> 0, 2 -> 1
        if direction_id_raw == "1":
            direction_id = 0
        elif direction_id_raw == "2":
            direction_id = 1
        else:
            raise ValueError(f"Invalid direction_id_raw: {direction_id_raw}")
        
        # map service type (example: "D1" -> service_type = 1)
        service_id = None
        
        for part in parts[1:]:
            if part.startswith("D") and len(part) > 1:
                try:
                    service_type = int(part[1:])
                    service_id = STCPParser.SERVICE_TYPE_MAP.get(service_type)
                    if service_id:
                        break
                except ValueError:
                    pass
        
        if not service_id:
            raise ValueError(f"Could not extract service_id from trip_id: {trip_id}")
        
        return {
            "route_id": route_id,
            "direction_id": direction_id,
            "service_id": service_id,
        }
    
    @staticmethod
    def parse_arrival(arrival_data: Dict[str, Any], stop_id: str, last_updated: datetime) -> Optional[Dict[str, Any]]:
        trip_id = arrival_data.get("trip_id")
        if not trip_id:
            return None
        
        try:
            trip_info = STCPParser.parse_trip_id(trip_id)
        except (ValueError, KeyError) as e:
            print(f"Error parsing trip_id {trip_id}: {e}")
            return None
        
        # Extract arrival time
        estimated_arrival_time_str = arrival_data.get("estimated_arrival_time")
        arrival_time = None
        if estimated_arrival_time_str:
            try:
                arrival_dt = datetime.fromisoformat(estimated_arrival_time_str.replace("Z", "+00:00"))
                arrival_time = arrival_dt.time()
            except (ValueError, AttributeError):
                pass
        
        # Extract other fields
        # vehicle_id can be None from API, use empty string for primary key
        vehicle_id = arrival_data.get("vehicle_id") or ""
        arrival_minutes = arrival_data.get("arrival_minutes")
        delay_minutes = arrival_data.get("delay_minutes")
        status = arrival_data.get("status")
        trip_headsign = arrival_data.get("trip_headsign")
        
        # minutes are represented as float
        if delay_minutes is not None:
            try:
                delay_minutes = float(delay_minutes)
            except (ValueError, TypeError):
                delay_minutes = None
        
        if arrival_minutes is not None:
            try:
                arrival_minutes = float(arrival_minutes)
            except (ValueError, TypeError):
                arrival_minutes = None
        
        return {
            "vehicle_id": vehicle_id,
            "stop_id": stop_id,
            "trip_number": "",  # trip_number is null from the API | TODO: Fill trip_number
            "route_id": trip_info["route_id"],
            "direction_id": trip_info["direction_id"],
            "service_id": trip_info["service_id"],
            "trip_headsign": trip_headsign,
            "stop_sequence": None,  # Not available in API response
            "arrival_time": arrival_time,
            "arrival_minutes": arrival_minutes,
            "delay_minutes": delay_minutes,
            "status": status,
            "last_updated": last_updated,
        }
    
    @staticmethod
    def parse_stop_realtime(stop_realtime_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        stop_id = stop_realtime_data.get("stop_id")
        if not stop_id:
            return []
        
        last_updated_str = stop_realtime_data.get("last_updated")
        if last_updated_str:
            try:
                last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                last_updated = datetime.utcnow()
        else:
            last_updated = datetime.utcnow()
        
        arrivals = stop_realtime_data.get("arrivals", [])
        parsed_arrivals = []
        
        for arrival in arrivals:
            parsed = STCPParser.parse_arrival(arrival, stop_id, last_updated)
            if parsed:
                parsed_arrivals.append(parsed)
        
        return parsed_arrivals