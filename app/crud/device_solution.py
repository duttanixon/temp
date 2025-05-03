from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.crud.base import CRUDBase
from app.models.device_solution import DeviceSolution, DeviceSolutionStatus
from app.schemas.device_solution import DeviceSolutionCreate, DeviceSolutionUpdate
import uuid
from datetime import datetime

class CRUDDeviceSolution(CRUDBase[DeviceSolution, DeviceSolutionCreate, DeviceSolutionUpdate]):
    def get_by_id(self, db: Session, *, id: uuid.UUID) -> Optional[DeviceSolution]:
        return db.query(DeviceSolution).filter(DeviceSolution.id == id).first()

    def get_by_device_and_solution(
        self, db: Session, *, device_id: uuid.UUID, solution_id: uuid.UUID
    ) -> Optional[DeviceSolution]:
        return db.query(DeviceSolution).filter(
            DeviceSolution.device_id == device_id,
            DeviceSolution.solution_id == solution_id
        ).first()
    
    def get_by_device(
        self, db: Session, *, device_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DeviceSolution]:
        return db.query(DeviceSolution).filter(
            DeviceSolution.device_id == device_id
        ).order_by(desc(DeviceSolution.created_at)).offset(skip).limit(limit).all()

    
    def get_by_solution(
        self, db: Session, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DeviceSolution]:
        return db.query(DeviceSolution).filter(
            DeviceSolution.solution_id == solution_id
        ).order_by(desc(DeviceSolution.created_at)).offset(skip).limit(limit).all()

    def get_active_by_device(
        self, db: Session, *, device_id: uuid.UUID
    ) -> List[DeviceSolution]:
        """Get all active solutions for a device"""
        return db.query(DeviceSolution).filter(
            DeviceSolution.device_id == device_id,
            DeviceSolution.status == DeviceSolutionStatus.ACTIVE
        ).all()
    
    
    def update_status(
        self, db: Session, *, id: uuid.UUID, status: DeviceSolutionStatus
    ) -> DeviceSolution:
        device_solution = self.get_by_id(db, id=id)
        device_solution.status = status
        if status == DeviceSolutionStatus.ACTIVE:
            device_solution.last_update = datetime.now()
        db.add(device_solution)
        db.commit()
        db.refresh(device_solution)
        return device_solution

    
    def update_metrics(
        self, db: Session, *, id: uuid.UUID, metrics: Dict[str, Any]
    ) -> DeviceSolution:
        device_solution = self.get_by_id(db, id=id)
        device_solution.metrics = metrics
        device_solution.last_update = datetime.now()
        db.add(device_solution)
        db.commit()
        db.refresh(device_solution)
        return device_solution

    
    def is_solution_running_on_device(
        self, db: Session, *, device_id: uuid.UUID, solution_id: uuid.UUID
    ) -> bool:
        """Check if a solution is actively running on a device"""
        device_solution = self.get_by_device_and_solution(
            db, device_id=device_id, solution_id=solution_id
        )
        return device_solution is not None and device_solution.status == DeviceSolutionStatus.ACTIVE

device_solution = CRUDDeviceSolution(DeviceSolution)