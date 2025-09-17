from typing import Any, Dict, Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from app.crud.base import CRUDBase
from app.models import User, UserRole, DeviceSolution, Device, Customer
from app.schemas.device_solution import DeviceSolutionCreate, DeviceSolutionUpdate
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

class CRUDDeviceSolution(CRUDBase[DeviceSolution, DeviceSolutionCreate, DeviceSolutionUpdate]):
    async def get_by_id(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[DeviceSolution]:
        result = await db.execute(select(DeviceSolution).filter(DeviceSolution.id == id))
        return result.scalars().first()

    async def get_by_device_and_solution(
        self, db: AsyncSession, *, device_id: uuid.UUID, solution_id: uuid.UUID
    ) -> Optional[DeviceSolution]:
        result = await db.execute(
            select(DeviceSolution).filter(
                DeviceSolution.device_id == device_id,
                DeviceSolution.solution_id == solution_id
            )
        )
        return result.scalars().first()
    
    async def get_by_device(
        self, db: AsyncSession, *, device_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DeviceSolution]:
        result = await db.execute(
            select(DeviceSolution).filter(
                DeviceSolution.device_id == device_id
            ).order_by(desc(DeviceSolution.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    
    async def get_by_solution(
        self, db: AsyncSession, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[DeviceSolution]:
        result = await db.execute(
            select(DeviceSolution).filter(
                DeviceSolution.solution_id == solution_id
            ).order_by(desc(DeviceSolution.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_device(
        self, db: AsyncSession, *, device_id: uuid.UUID
    ) -> List[DeviceSolution]:
        """Get all active solutions for a device"""
        result = await db.execute(
            select(DeviceSolution).filter(
                DeviceSolution.device_id == device_id,
            )
        )
        return list(result.scalars().all())
    
    async def get_devices_by_solution_with_details(
        self, db: AsyncSession, *, solution_id: uuid.UUID, current_user: User, solution_name: str, solution_description: str
    ) -> List[Dict[str, Any]]:
        """
        Get devices using a specific solution with joined details.
        """
        query = (
            select(
                DeviceSolution,
                Device.name.label("device_name"),
                Device.location.label("device_location"),
                Device.customer_id,
                Customer.name.label("customer_name"),
            )
            .join(Device, DeviceSolution.device_id == Device.device_id)
            .join(Customer, Device.customer_id == Customer.customer_id)
            .filter(DeviceSolution.solution_id == solution_id)
        )

        # Filter based on user role
        if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
            if not current_user.customer_id:
                return []
            query = query.filter(Device.customer_id == current_user.customer_id)
        
        results = (await db.execute(query)).all()

        response_data = []
        for result in results:
            (ds, device_name, device_location, customer_id, customer_name) = result

            detail_view = {
                "id": ds.id,
                "device_id": ds.device_id,
                "device_name": device_name,
                "device_location": device_location,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "solution_id": ds.solution_id,
                "configuration": ds.configuration,
                "last_update": ds.last_update,
                "created_at": ds.created_at,
                "updated_at": ds.updated_at,
                "solution_name": solution_name,
                "solution_description": solution_description,
                "metrics": ds.metrics if hasattr(ds, 'metrics') else None,
            }
            response_data.append(detail_view)
        
        return response_data

    async def update_metrics(
        self, db: AsyncSession, *, id: uuid.UUID, metrics: Dict[str, Any]
    ) -> DeviceSolution:
        device_solution = await self.get_by_id(db, id=id)
        device_solution.metrics = metrics
        device_solution.last_update = datetime.now(ZoneInfo("Asia/Tokyo"))
        db.add(device_solution)
        await db.commit()
        await db.refresh(device_solution)
        return device_solution

device_solution = CRUDDeviceSolution(DeviceSolution)
