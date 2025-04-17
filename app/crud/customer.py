from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.customer import Customer, CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerUpdate
import uuid


class CRUDCustomer(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
    def get_by_id(self, db: Session, *, customer_id: uuid.UUID) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.name == name).first()
    
    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Customer]:
        return db.query(Customer).filter(Customer.status == CustomerStatus.ACTIVE).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CustomerCreate) -> Customer:
        db_obj = Customer(
            name=obj_in.name,
            contact_email=obj_in.contact_email,
            address=obj_in.address,
            status=obj_in.status or CustomerStatus.ACTIVE
        )
        db.add(db_obj)
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


customer = CRUDCustomer(Customer)
