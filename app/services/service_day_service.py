from typing import List, Optional
from datetime import date
import json
from sqlalchemy.orm import Session
from app.data_source.gtfs.stcp.models.service_day import ServiceDay as ServiceDayModel
from app.api.schemas.service_day import ServiceDay


class ServiceDayService:
    
    @staticmethod
    def _model_to_schema(db_service_day: ServiceDayModel) -> ServiceDay:
        return ServiceDay(
            service_id=db_service_day.service_id,
            service_name=db_service_day.service_name,
            service_type=db_service_day.service_type,
            day_map=db_service_day.day_map,
            start_date=db_service_day.start_date,
            end_date=db_service_day.end_date
        )
    
    @staticmethod
    def get_service_day_by_id_or_type(db: Session, identifier: str) -> Optional[ServiceDay]:
        # allows both service_id and service_type as IDs

        # Try as service_id
        db_service_day = db.query(ServiceDayModel).filter(ServiceDayModel.service_id == identifier).first()
        if db_service_day:
            return ServiceDayService._model_to_schema(db_service_day)
        
        # If not found, try as service_type
        try:
            service_type = int(identifier)
            db_service_day = db.query(ServiceDayModel).filter(ServiceDayModel.service_type == service_type).first()
            if db_service_day:
                return ServiceDayService._model_to_schema(db_service_day)
        except ValueError:
            pass
        
        return None
    
    @staticmethod
    def get_service_days(db: Session) -> List[ServiceDay]:
        db_service_days = db.query(ServiceDayModel).all()
        return [ServiceDayService._model_to_schema(sd) for sd in db_service_days]

    @staticmethod
    def get_current_service_id(db: Session, on_date: Optional[date] = None) -> Optional[str]:
        """
        Resolve the GTFS service_id that applies for the given date (defaults to today).
        
        Ignores both start_date and end_date completely. Matches based solely on:
        - day_map weekday flag matches target weekday
        
        If multiple service days match, returns the one with the latest start_date.
        """
        target_date = on_date or date.today()
        weekday_idx = target_date.weekday()  # Monday=0 ... Sunday=6
        
        # Query all service days (ignore both start_date and end_date)
        all_service_days = db.query(ServiceDayModel).all()
        
        best = None
        for sd in all_service_days:
            try:
                day_map = json.loads(sd.day_map) if isinstance(sd.day_map, str) else sd.day_map
                if not (isinstance(day_map, list) and len(day_map) >= 7 and int(day_map[weekday_idx]) == 1):
                    continue
                # Prefer service day with latest start_date (most recent service definition)
                if best is None or (sd.start_date and sd.start_date > best.start_date):
                    best = sd
            except (ValueError, TypeError, IndexError):
                continue
        
        if best:
            return best.service_id
        
        return None