from typing import List, Optional
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