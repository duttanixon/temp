from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.core.config import settings
from app.utils.aws_iot import iot_core
from app.models.customer import Customer, CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
import uuid



from app.utils.logger import get_logger
logger = get_logger(__name__)

class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def get_by_id(self, db: Session, *, customer_id: uuid.UUID) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.name == name).first()
    
    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Customer]:
        return db.query(Customer).filter(Customer.status == CustomerStatus.ACTIVE).offset(skip).limit(limit).all()

    def get_by_email(self, db: Session, *, contact_email: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.contact_email == contact_email).first()

    def create(self, db: Session, *, obj_in: CustomerCreate) -> Customer:
        db_obj = Customer(
            name=obj_in.name,
            contact_email=obj_in.contact_email,
            address=obj_in.address,
            status=obj_in.status or CustomerStatus.ACTIVE
        )
        db.add(db_obj)
        db.flush()  # Flush to get the ID without committing

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

        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def suspend(self, db: Session, *, customer_id: uuid.UUID) -> Customer:
        customer = self.get_by_id(db, customer_id=customer_id)
        customer.status = CustomerStatus.SUSPENDED
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    
    def activate(self, db: Session, *, customer_id: uuid.UUID) -> Customer:
        customer = self.get_by_id(db, customer_id=customer_id)
        customer.status = CustomerStatus.ACTIVE
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    
    def remove(self, db: Session, *, customer_id: uuid.UUID) -> Customer:
        """
        Delete a customer by ID
        """
        customer = self.get_by_id(db, customer_id=customer_id)
        if not customer:
            return None
        
        # Check if we need to clean up IoT resources
        if settings.IOT_ENABLED and customer.iot_thing_group_name:
            try:
                logger.info(f"Deleting IoT thing group: {customer.iot_thing_group_name}")
                iot_core.delete_customer_thing_group(customer.iot_thing_group_name)
            except Exception as e:
                logger.error(f"Error deleting IoT thing group: {str(e)}")

        db.delete(customer)
        db.commit()
        return customer


customer = CRUDCustomer(Customer)
