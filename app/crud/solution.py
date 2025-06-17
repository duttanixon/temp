from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from sqlalchemy.dialects.postgresql import JSONB
from app.crud.base import CRUDBase
from app.models import DeviceSolution, CustomerSolution, Solution, SolutionStatus
from app.schemas.solution import SolutionCreate, SolutionUpdate
import uuid

class CRUDSolution(CRUDBase[Solution, SolutionCreate, SolutionUpdate]):
    def get_by_id(self, db: Session, *, solution_id: uuid.UUID) -> Optional[Solution]:
        return db.query(Solution).filter(Solution.solution_id == solution_id).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Solution]:
        return db.query(Solution).filter(Solution.name == name).first()

    
    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Solution]:
        """Get all active solutions"""
        return db.query(Solution).filter(
            Solution.status == SolutionStatus.ACTIVE
        ).offset(skip).limit(limit).all()

    
    # def get_compatible_with_device_type(self, db: Session, *, device_type: str, skip: int = 0, limit: int = 100) -> List[Solution]:
    #     """Get solutions compatible with a specific device type"""
    #     # JSON contains array check - PostgreSQL specific
    #     return db.query(Solution).filter(
    #         Solution.compatibility.cast(JSONB).op('?')(device_type)
    #     ).offset(skip).limit(limit).all()
    
    def get_compatible_with_device_type(self, db: Session, *, device_type: str, skip: int = 0, limit: int = 100) -> List[Solution]:
        """Get solutions compatible with a specific device type"""
        solutions = db.query(Solution).all()
        compatible_solutions = [
            sol for sol in solutions 
            if sol.compatibility and device_type in sol.compatibility
        ]
        return compatible_solutions[skip:skip+limit]

    def get_with_customer_count(self, db: Session, *, solution_id: uuid.UUID) -> Optional[Dict]:
        """Get solution with count of customers using it"""
        solution = self.get_by_id(db, solution_id=solution_id)
        if not solution:
            return None
            
        # Get customer count
        customer_count = db.query(func.count(CustomerSolution.customer_id.distinct())).filter(
            CustomerSolution.solution_id == solution_id
        ).scalar()
        
        # Get device count
        device_count = db.query(func.count(DeviceSolution.device_id.distinct())).filter(
            DeviceSolution.solution_id == solution_id
        ).scalar()
        
        # Combine data
        result = solution.__dict__.copy()
        result["customers_count"] = customer_count or 0
    #     result["devices_count"] = device_count or 0
        
        return result

    
    def deprecate(self, db: Session, *, solution_id: uuid.UUID) -> Solution:
        """Mark a solution as deprecated"""
        solution = self.get_by_id(db, solution_id=solution_id)
        solution.status = SolutionStatus.DEPRECATED
        db.add(solution)
        db.commit()
        db.refresh(solution)
        return solution

    def activate(self, db: Session, *, solution_id: uuid.UUID) -> Solution:
        """Mark a solution as active"""
        solution = self.get_by_id(db, solution_id=solution_id)
        solution.status = SolutionStatus.ACTIVE
        db.add(solution)
        db.commit()
        db.refresh(solution)
        return solution

solution = CRUDSolution(Solution)