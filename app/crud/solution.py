from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.crud.base import CRUDBase
from app.models import DeviceSolution, CustomerSolution, Solution
from app.schemas.solution import SolutionCreate, SolutionUpdate
import uuid

class CRUDSolution(CRUDBase[Solution, SolutionCreate, SolutionUpdate]):
    async def get_by_id(self, db: AsyncSession, *, solution_id: uuid.UUID) -> Optional[Solution]:
        result = await db.execute(select(Solution).filter(Solution.solution_id == solution_id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Solution]:
        result = await db.execute(select(Solution).filter(Solution.name == name))
        return result.scalars().first()

    async def get_by_ids(self, db: AsyncSession, *, ids: List[uuid.UUID]) -> List[Solution]:
        """Get multiple solutions by their IDs."""
        result = await db.execute(select(Solution).filter(Solution.solution_id.in_(ids)))
        return list(result.scalars().all())
    
    async def get_compatible_with_device_type(self, db: AsyncSession, *, device_type: str, skip: int = 0, limit: int = 100) -> List[Solution]:
        """Get solutions compatible with a specific device type"""
        result = await db.execute(
            select(Solution)
            .filter(Solution.compatibility.contains([device_type]))
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_customer_count(self, db: AsyncSession, *, solution_id: uuid.UUID) -> Optional[Dict]:
        """Get solution with count of customers using it"""
        solution_obj = await self.get_by_id(db, solution_id=solution_id)
        if not solution_obj:
            return None
            
        # Get customer count
        customer_count_result = await db.execute(
            select(func.count(CustomerSolution.customer_id.distinct())).filter(
                CustomerSolution.solution_id == solution_id
            )
        )
        customer_count = customer_count_result.scalar()
        
        # Get device count
        device_count_result = await db.execute(
            select(func.count(DeviceSolution.device_id.distinct())).filter(
                DeviceSolution.solution_id == solution_id
            )
        )
        device_count = device_count_result.scalar()
        
        # Combine data
        result = solution_obj.__dict__.copy()
        result["customers_count"] = customer_count or 0
        result["devices_count"] = device_count or 0
        
        return result


solution = CRUDSolution(Solution)
