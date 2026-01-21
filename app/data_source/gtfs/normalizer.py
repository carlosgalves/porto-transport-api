import json
from datetime import datetime, time, timedelta
from typing import List, Dict, Any


class GTFSNormalizer:
    
    SERVICE_MAPPING = {
        # service_id: (service_code, service_name, service_type)
        "UTEIS": ("U", "UTEIS", 1),
        "SAB": ("S", "SAB", 2),
        "DOM": ("D", "DOM", 3),
        "U": ("U", "UTEIS", 1),
        "S": ("S", "SAB", 2),
        "D": ("D", "DOM", 3),
        # These are currently unused by STCP
        "ELECUTEIS": ("I", "ELECUTEIS", None),
        "ELECSAB": ("J", "ELECSAB", None),
        "ELECDOM": ("K", "ELECDOM", None),
        "DOMFE": ("H", "DOMFE", 3),
        "SABFE": ("G", "SABFE", 3),
        "UTEISFE": ("F", "UTEISFE", 3),
    }

    @staticmethod
    def normalize_agency(gtfs_agency: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": gtfs_agency.get("agency_id").strip(),
            "name": gtfs_agency.get("agency_name").strip(),
            "url": gtfs_agency.get("agency_url").strip(),
        }

    @staticmethod
    def normalize_agencies(gtfs_agencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_agency(agency) for agency in gtfs_agencies]
    

    @staticmethod
    def normalize_stop(gtfs_stop: Dict[str, Any]) -> Dict[str, Any]:
        stop_code = gtfs_stop.get("stop_code").strip()
        stop_id = gtfs_stop.get("stop_id").strip()
        
        normalized_id = stop_code
        
        return {
            "id": normalized_id,
            "name": gtfs_stop.get("stop_name").strip(),
            "lat": float(gtfs_stop.get("stop_lat")),
            "lon": float(gtfs_stop.get("stop_lon")),
            "zone_id": gtfs_stop.get("zone_id").strip(),
        }
    
    @staticmethod
    def normalize_stops(gtfs_stops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_stop(stop) for stop in gtfs_stops]
    

    @staticmethod
    def normalize_calendar(gtfs_calendar: Dict[str, Any]) -> Dict[str, Any]:
        service_id_raw = gtfs_calendar.get("service_id").strip()
        
        mapping = GTFSNormalizer.SERVICE_MAPPING.get(service_id_raw)
        if not mapping:
            raise ValueError(f"Unknown service_id: {service_id_raw}")
        
        service_code, service_name, service_type = mapping
        
        # matching day names will become 1, non-matching will become 0
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_map = [
            int(gtfs_calendar.get(day_name, "0"))
            for day_name in day_names
        ]
        
        start_date_str = gtfs_calendar.get("start_date", "").strip()
        end_date_str = gtfs_calendar.get("end_date", "").strip()
        
        start_date = datetime.strptime(start_date_str, "%Y%m%d").date()
        end_date = datetime.strptime(end_date_str, "%Y%m%d").date()
        
        return {
            "service_id": service_code,
            "service_name": service_name,
            "service_type": service_type,
            "day_map": json.dumps(day_map), # array of 1 and 0
            "start_date": start_date,
            "end_date": end_date,
        }
    
    @staticmethod
    def normalize_calendars(gtfs_calendars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_calendar(cal) for cal in gtfs_calendars]
    

    
    @staticmethod
    def normalize_route(gtfs_route: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": gtfs_route.get("route_id").strip(),
            "short_name": gtfs_route.get("route_short_name").strip(),
            "long_name": gtfs_route.get("route_long_name").strip(),
            "type": int(gtfs_route.get("route_type")),
            "route_color": gtfs_route.get("route_color").strip(),
            "route_text_color": gtfs_route.get("route_text_color").strip(),
        }
    
    @staticmethod
    def normalize_routes(gtfs_routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_route(route) for route in gtfs_routes]
    

    @staticmethod
    def normalize_trip(gtfs_trip: Dict[str, Any]) -> Dict[str, Any]:
        service_id_raw = gtfs_trip.get("service_id").strip()
        
        # normalize service_id
        mapping = GTFSNormalizer.SERVICE_MAPPING.get(service_id_raw)
        if not mapping:
            raise ValueError(f"Unknown service_id: {service_id_raw}")
        
        service_code, _, _ = mapping
        
        return {
            "route_id": gtfs_trip.get("route_id").strip(),
            "direction_id": int(gtfs_trip.get("direction_id")),
            "service_id": service_code,
            "headsign": gtfs_trip.get("trip_headsign").strip(),
        }
    
    @staticmethod
    def normalize_trips(gtfs_trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_trip(trip) for trip in gtfs_trips]
    
    @staticmethod
    def normalize_trip_for_table(gtfs_trip: Dict[str, Any]) -> Dict[str, Any]:
        service_id_raw = gtfs_trip.get("service_id").strip()
        
        # normalize service_id
        mapping = GTFSNormalizer.SERVICE_MAPPING.get(service_id_raw)
        if not mapping:
            raise ValueError(f"Unknown service_id: {service_id_raw}")
        
        service_code, _, _ = mapping
        
        # Extract trip_number from trip_id (e.g., "107_0_U_29" -> "29")
        trip_id_raw = gtfs_trip.get("trip_id").strip()
        trip_number = trip_id_raw.split("_")[-1] if trip_id_raw else ""
        
        route_id = gtfs_trip.get("route_id").strip()
        direction_id = int(gtfs_trip.get("direction_id"))
        
        # Create trip_id by joining: route_id + _ + direction_id + _ + service_id + _ + trip_number
        trip_id = f"{route_id}_{direction_id}_{service_code}_{trip_number}"
        
        wheelchair_accessible_str = gtfs_trip.get("wheelchair_accessible", "").strip()
        if wheelchair_accessible_str:
            wheelchair_accessible = int(wheelchair_accessible_str) == 1
        else:
            wheelchair_accessible = False
        
        return {
            "trip_id": trip_id,
            "route_id": route_id,
            "direction_id": direction_id,
            "service_id": service_code,
            "trip_number": trip_number,
            "headsign": gtfs_trip.get("trip_headsign").strip(),
            "wheelchair_accessible": wheelchair_accessible,
        }
    
    @staticmethod
    def normalize_trips_for_table(gtfs_trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_trip_for_table(trip) for trip in gtfs_trips]


    @staticmethod
    def normalize_shape(gtfs_shape: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": gtfs_shape.get("shape_id").strip(),
            "lat": float(gtfs_shape.get("shape_pt_lat")),
            "lon": float(gtfs_shape.get("shape_pt_lon")),
            "sequence": int(gtfs_shape.get("shape_pt_sequence")),
        }

    @staticmethod
    def normalize_shapes(gtfs_shapes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_shape(shape) for shape in gtfs_shapes]

    @staticmethod
    def normalize_trip_shape(gtfs_trip: Dict[str, Any]) -> Dict[str, Any]:
        trip_id = gtfs_trip.get("trip_id").strip()
        shape_id = gtfs_trip.get("shape_id", "").strip()
        
        return {
            "trip_id": trip_id,
            "shape_id": shape_id,
        }

    @staticmethod
    def normalize_trip_shapes(gtfs_trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        trip_shapes = []
        for trip in gtfs_trips:
            normalized = GTFSNormalizer.normalize_trip_shape(trip)
            if normalized:
                trip_shapes.append(normalized)
        return trip_shapes



    @staticmethod
    def normalize_stop_time(gtfs_stop_time: Dict[str, Any]) -> Dict[str, Any]:
        trip_id = gtfs_stop_time.get("trip_id").strip()
        
        # Parse trip_id to extract route_id, direction_id, service_id, trip_number
        # Format: route_id + _ + direction_id + _ + service_id + _ + trip_number
        parts = trip_id.split("_")
        if len(parts) < 4:
            raise ValueError(f"Invalid trip_id format: {trip_id}")
        
        route_id = parts[0]
        direction_id = int(parts[1])
        service_id = parts[2]
        trip_number = parts[3]
        
        stop_id = gtfs_stop_time.get("stop_id").strip()
        stop_sequence = int(gtfs_stop_time.get("stop_sequence"))
        
        # Parse time strings (format: "H:MM:SS" or "HH:MM:SS")
        # GTFS allows times > 24 hours (e.g., 25:30:00 meaning 1:00 for the next day but same service day),
        # For isntance, a bus may have it's last trip ending after midnight, even though it's part ofthe same service day.
        arrival_time_str = gtfs_stop_time.get("arrival_time").strip()
        departure_time_str = gtfs_stop_time.get("departure_time").strip()
        
        def parse_gtfs_time(time_str: str) -> time:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) > 2 else 0
            
            # Normalize hours to 0-23 range
            hours = hours % 24
            
            return time(hours, minutes, seconds)
        
        arrival_time = parse_gtfs_time(arrival_time_str)
        departure_time = parse_gtfs_time(departure_time_str)
        
        return {
            "trip_id": trip_id,
            "route_id": route_id,
            "direction_id": direction_id,
            "service_id": service_id,
            "trip_number": trip_number,
            "stop_id": stop_id,
            "stop_sequence": stop_sequence,
            "arrival_time": arrival_time,
            "departure_time": departure_time,
        }

    @staticmethod
    def normalize_stop_times(gtfs_stop_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_stop_time(stop_time) for stop_time in gtfs_stop_times]