import json
from datetime import datetime, time, timedelta
from typing import List, Dict, Any
import unicodedata


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
    REALTIME_D_SERVICE_MAP = {
        1: "U",
        2: "S",
        3: "D",
        6: "U",
    }

    @staticmethod
    def _canonical_text(value: str) -> str:
        value = unicodedata.normalize("NFD", value or "")
        value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
        return " ".join(value.upper().strip().split())

    @staticmethod
    def _resolve_service_mapping(service_id_raw: str, trip_id_raw: str = "") -> tuple[str, str, Any]:
        raw = (service_id_raw or "").strip()
        if raw in GTFSNormalizer.SERVICE_MAPPING:
            return GTFSNormalizer.SERVICE_MAPPING[raw]

        normalized = GTFSNormalizer._canonical_text(raw)
        normalized = normalized.replace("|", " ")

        if "UTEI" in normalized:
            return ("U", "UTEIS", 1)
        if "SAB" in normalized:
            return ("S", "SAB", 2)
        if "DOM" in normalized or "FERIAD" in normalized:
            return ("D", "DOM", 3)

        # Fallback from realtime-style trip id tokens (e.g. ...|D6|...)
        if "|" in (trip_id_raw or ""):
            for part in trip_id_raw.split("|"):
                if part.startswith("D") and len(part) > 1:
                    try:
                        service_type = int(part[1:])
                    except ValueError:
                        continue
                    mapped = GTFSNormalizer.REALTIME_D_SERVICE_MAP.get(service_type)
                    if mapped == "U":
                        return ("U", "UTEIS", 1)
                    if mapped == "S":
                        return ("S", "SAB", 2)
                    if mapped == "D":
                        return ("D", "DOM", 3)

        raise ValueError(f"Unknown service_id: {service_id_raw}")

    @staticmethod
    def _parse_trip_identity(gtfs_trip_id: str, service_id_raw: str = "") -> Dict[str, Any]:
        trip_id_raw = (gtfs_trip_id or "").strip()
        if "|" in trip_id_raw:
            # New format: 304_0_2|218|D6|T2|N17
            first_part = trip_id_raw.split("|")[0]
            parts = first_part.split("_")
            if len(parts) < 3:
                raise ValueError(f"Invalid trip_id format: {trip_id_raw}")
            route_id = parts[0]
            direction_id_raw = parts[2]
            if direction_id_raw == "1":
                direction_id = 0
            elif direction_id_raw == "2":
                direction_id = 1
            else:
                try:
                    direction_id = int(direction_id_raw)
                except ValueError as exc:
                    raise ValueError(f"Invalid direction_id in trip_id: {trip_id_raw}") from exc

            trip_number = ""
            # Prefer N* token (run instance) over T* token.
            for part in trip_id_raw.split("|"):
                if part.startswith("N") and len(part) > 1:
                    trip_number = part[1:]
                    break
            for part in trip_id_raw.split("|"):
                if not trip_number and part.startswith("T") and len(part) > 1:
                    trip_number = part[1:]
                    break
            if not trip_number:
                trip_number = trip_id_raw.split("|")[-1]

            service_code, _, _ = GTFSNormalizer._resolve_service_mapping(service_id_raw, trip_id_raw)
            normalized_trip_id = f"{route_id}_{direction_id}_{service_code}_{trip_number}"
            return {
                "trip_id": normalized_trip_id,
                "route_id": route_id,
                "direction_id": direction_id,
                "service_id": service_code,
                "trip_number": trip_number,
            }

        # Legacy format: route_direction_service_tripNumber
        parts = trip_id_raw.split("_")
        if len(parts) < 4:
            raise ValueError(f"Invalid trip_id format: {trip_id_raw}")
        route_id = parts[0]
        direction_id = int(parts[1])
        service_code, _, _ = GTFSNormalizer._resolve_service_mapping(service_id_raw or parts[2], trip_id_raw)
        trip_number = parts[3]
        normalized_trip_id = f"{route_id}_{direction_id}_{service_code}_{trip_number}"
        return {
            "trip_id": normalized_trip_id,
            "route_id": route_id,
            "direction_id": direction_id,
            "service_id": service_code,
            "trip_number": trip_number,
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
        
        service_code, service_name, service_type = GTFSNormalizer._resolve_service_mapping(service_id_raw)
        
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
        
        service_code, _, _ = GTFSNormalizer._resolve_service_mapping(
            service_id_raw,
            gtfs_trip.get("trip_id", "").strip(),
        )
        
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
        trip_identity = GTFSNormalizer._parse_trip_identity(
            gtfs_trip.get("trip_id").strip(),
            service_id_raw,
        )
        
        wheelchair_accessible_str = gtfs_trip.get("wheelchair_accessible", "").strip()
        if wheelchair_accessible_str:
            wheelchair_accessible = int(wheelchair_accessible_str) == 1
        else:
            wheelchair_accessible = False
        
        return {
            "trip_id": trip_identity["trip_id"],
            "route_id": trip_identity["route_id"],
            "direction_id": trip_identity["direction_id"],
            "service_id": trip_identity["service_id"],
            "trip_number": trip_identity["trip_number"],
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
        trip_identity = GTFSNormalizer._parse_trip_identity(
            gtfs_trip.get("trip_id").strip(),
            gtfs_trip.get("service_id", "").strip(),
        )
        shape_id = gtfs_trip.get("shape_id", "").strip()
        
        return {
            "trip_id": trip_identity["trip_id"],
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
        trip_identity = GTFSNormalizer._parse_trip_identity(gtfs_stop_time.get("trip_id").strip())
        
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
            "trip_id": trip_identity["trip_id"],
            "route_id": trip_identity["route_id"],
            "direction_id": trip_identity["direction_id"],
            "service_id": trip_identity["service_id"],
            "trip_number": trip_identity["trip_number"],
            "stop_id": stop_id,
            "stop_sequence": stop_sequence,
            "arrival_time": arrival_time,
            "departure_time": departure_time,
        }

    @staticmethod
    def normalize_stop_times(gtfs_stop_times: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [GTFSNormalizer.normalize_stop_time(stop_time) for stop_time in gtfs_stop_times]