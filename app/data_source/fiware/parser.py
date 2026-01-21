from typing import List, Dict, Any, Optional
from datetime import datetime


class FIWAREParser:
    
    @staticmethod
    def extract_annotation_value(annotations: List[str], prefix: str) -> Optional[str]:
        for annotation in annotations:
            if annotation.startswith(prefix):
                return annotation.split(":", 2)[-1]  # Get everything after the prefix
        return None
    
    @staticmethod
    def parse_vehicle(vehicle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        vehicle_id = vehicle_data.get("fleetVehicleId", {}).get("value")
        if not vehicle_id:
            return None
                
        annotations = vehicle_data.get("annotations", {}).get("value", [])
        route_id = FIWAREParser.extract_annotation_value(annotations, "stcp:route:")
        direction_id = FIWAREParser.extract_annotation_value(annotations, "stcp:sentido:")

        nr_viagem = FIWAREParser.extract_annotation_value(annotations, "stcp:nr_viagem:")
        
        service_id = None
        
        if nr_viagem:
            parts = nr_viagem.split("|")
            for part in parts:
                if part.startswith("D") and len(part) > 1:
                    try:
                        service_type = int(part[1:])  # Extract number after 'D'
                        if service_type == 1:
                            service_id = "U"
                        elif service_type == 2:
                            service_id = "S"
                        elif service_type == 3:
                            service_id = "D"
                    except ValueError:
                        pass
                    break
                
        location = vehicle_data.get("location", {}).get("value", {})
        coordinates = location.get("coordinates", [])
        lon = float(coordinates[0])
        lat = float(coordinates[1])

        heading = vehicle_data.get("heading", {}).get("value")
        speed = vehicle_data.get("speed", {}).get("value")
        
        observation_datetime_str = vehicle_data.get("observationDateTime", {}).get("value")
        last_updated = datetime.utcnow()
        if observation_datetime_str:
            try:
                last_updated = datetime.fromisoformat(observation_datetime_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                last_updated = datetime.utcnow()
        
        return {
            "vehicle_id": vehicle_id,
            "route_id": route_id,
            "direction_id": direction_id,
            "service_id": service_id,
            "lat": lat,
            "lon": lon,
            "heading": heading,
            "speed": speed,
            "last_updated": last_updated
        }
    

    @staticmethod
    def parse_vehicles(vehicles_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        parsed_vehicles = []
        for vehicle in vehicles_data:
            parsed = FIWAREParser.parse_vehicle(vehicle)
            if parsed:
                parsed_vehicles.append(parsed)
        return parsed_vehicles