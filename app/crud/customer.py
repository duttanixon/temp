from typing import Any, Dict, Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.core.config import settings
from app.utils.aws_iot import iot_core
from app.models.customer import Customer, CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
import uuid

from app.utils.logger import get_logger
logger = get_logger(__name__)

class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    async def get_by_id(self, db: AsyncSession, *, customer_id: uuid.UUID) -> Optional[Customer]:
        result = await db.execute(select(Customer).filter(Customer.customer_id == customer_id))
        return result.scalars().first()
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Customer]:
        result = await db.execute(select(Customer).filter(Customer.name == name))
        return result.scalars().first()
    
    async def get_active(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Customer]:
        result = await db.execute(
            select(Customer)
            .filter(Customer.status == CustomerStatus.ACTIVE)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_email(self, db: AsyncSession, *, contact_email: str) -> Optional[Customer]:
        result = await db.execute(select(Customer).filter(Customer.contact_email == contact_email))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: CustomerCreate) -> Customer:
        db_obj = Customer(
            name=obj_in.name,
            contact_email=obj_in.contact_email,
            address=obj_in.address,
            status=obj_in.status or CustomerStatus.ACTIVE
        )
        db.add(db_obj)
        await db.flush()  # Flush to get the ID without committing

        # Create IoT Thing Group if IoT is enabled
        if settings.IOT_ENABLED:
            try:
                thing_group_info = iot_core.create_customer_thing_group(
                    customer_name=db_obj.name,
                    customer_id=db_obj.customer_id
                )
                db_obj.iot_thing_group_name = thing_group_info["thing_group_name"]
                db_obj.iot_thing_group_arn = thing_group_info["thing_group_arn"]
            except Exception as e:
                # Log the error but continue with customer creation
                # This makes IoT integration non-blocking for customer creation
                logger.error(f"Error creating IoT thing group: {str(e)}")

        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def suspend(self, db: AsyncSession, *, customer_id: uuid.UUID) -> Customer:
        customer = await self.get_by_id(db, customer_id=customer_id)
        if customer:
            customer.status = CustomerStatus.SUSPENDED
            db.add(customer)
            await db.commit()
            await db.refresh(customer)
        return customer
    
    async def activate(self, db: AsyncSession, *, customer_id: uuid.UUID) -> Customer:
        customer = await self.get_by_id(db, customer_id=customer_id)
        if customer:
            customer.status = CustomerStatus.ACTIVE
            db.add(customer)
            await db.commit()
            await db.refresh(customer)
        return customer
    
    async def remove(self, db: AsyncSession, *, customer_id: uuid.UUID) -> Optional[Customer]:
        """
        Delete a customer by ID
        """
        customer_obj = await self.get_by_id(db, customer_id=customer_id)
        if not customer_obj:
            return None
        
        # Check if we need to clean up IoT resources
        if settings.IOT_ENABLED and customer_obj.iot_thing_group_name:
            try:
                logger.info(f"Deleting IoT thing group: {customer_obj.iot_thing_group_name}")
                iot_core.delete_customer_thing_group(customer_obj.iot_thing_group_name)
            except Exception as e:
                logger.error(f"Error deleting IoT thing group: {str(e)}")

        await db.delete(customer_obj)
        await db.commit()
        return customer_obj
    
    async def get_by_ids(self, db: AsyncSession, *, ids: List[uuid.UUID]) -> List[Customer]:
        """Get multiple customers by their IDs"""
        result = await db.execute(select(Customer).filter(Customer.customer_id.in_(ids)))
        return list(result.scalars().all())

customer = CRUDCustomer(Customer)
