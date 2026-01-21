import csv
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import logging

from app.data_source.gtfs.normalizer import GTFSNormalizer

logger = logging.getLogger(__name__)


class GTFSLoaderError(Exception):
    pass


class GTFSFileNotFoundError(GTFSLoaderError):
    pass


class GTFSLoader:
    def __init__(self, data_dir: Path):

        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise GTFSFileNotFoundError(f"GTFS data directory not found: {data_dir}")
        
        if not self.data_dir.is_dir():
            raise GTFSLoaderError(f"Path is not a directory: {data_dir}")
        
        self.normalizer = GTFSNormalizer()

    def _load_csv_file(self, filename: str) -> List[Dict[str, str]]:
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            raise GTFSFileNotFoundError(f"{filename} not found at {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [dict(row) for row in reader]
                
            logger.debug(f"Loaded {len(rows)} rows from {filename}")
            return rows
            
        except UnicodeDecodeError as e:
            raise GTFSLoaderError(f"Error decoding {filename}: {e}") from e
        except csv.Error as e:
            raise GTFSLoaderError(f"Error parsing CSV file {filename}: {e}") from e
        except IOError as e:
            raise GTFSLoaderError(f"Error reading file {filename}: {e}") from e

    def _load_and_normalize(
        self, 
        filename: str, 
        normalize_func: Callable[[List[Dict[str, str]]], List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        raw_data = self._load_csv_file(filename)
        normalized_data = normalize_func(raw_data)
        logger.info(f"Normalized {len(normalized_data)} records from {filename}")
        return normalized_data

    def load_agency(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("agency.txt", self.normalizer.normalize_agencies)
    
    def load_stops(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("stops.txt", self.normalizer.normalize_stops)
    
    def load_calendar(self) -> List[Dict[str, Any]]:

        return self._load_and_normalize("calendar.txt", self.normalizer.normalize_calendars)
    
    def load_routes(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("routes.txt", self.normalizer.normalize_routes)
    
    def load_trips(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("trips.txt", self.normalizer.normalize_trips)

    def load_shapes(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("shapes.txt", self.normalizer.normalize_shapes)

    def load_trip_shapes(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("trips.txt", self.normalizer.normalize_trip_shapes)

    def load_stop_times(self) -> List[Dict[str, Any]]:
        return self._load_and_normalize("stop_times.txt", self.normalizer.normalize_stop_times)
    
    def validate_gtfs_files(self) -> bool:
        required_files = ["agency.txt", "calendar.txt", "routes.txt", "shapes.txt", "stop_times.txt", "stops.txt", "trips.txt"]
        missing_files = []
        
        for filename in required_files:
            file_path = self.data_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        if missing_files:
            raise GTFSFileNotFoundError(
                f"Missing required GTFS files: {', '.join(missing_files)}"
            )
        
        logger.info("GTFS feed validation passed")
        return True