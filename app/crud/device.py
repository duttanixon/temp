from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.crud.base import CRUDBase
from app.models.device import Device, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate
import uuid

class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def get_by_id(self, db: Session, *, device_id: uuid.UUID) -> Optional[Device]:
        return db.query(Device).filter(Device.device_id == device_id).first()
    
    def get_by_mac_address(self, db: Session, *, mac_address: str) -> Optional[Device]:
        if not mac_address:
            return None
        return db.query(Device).filter(Device.mac_address == mac_address).first()
    
    def get_by_thing_name(self, db: Session, *, thing_name: str) -> Optional[Device]:
        return db.query(Device).filter(Device.thing_name == thing_name).first()

    def get_by_customer(
        self, db: Session, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        return db.query(Device).filter(
            Device.customer_id == customer_id
        ).order_by(desc(Device.created_at)).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: DeviceCreate, device_name: str) -> Device:
        db_obj = Device(
            name=device_name,
            description=obj_in.description,
            mac_address=obj_in.mac_address,
            serial_number=obj_in.serial_number,
            device_type=obj_in.device_type,
            firmware_version=obj_in.firmware_version,
            ip_address=obj_in.ip_address,
            location=obj_in.location,
            customer_id=obj_in.customer_id,
            configuration=obj_in.configuration,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


    def update_device_status(
        self, db: Session, *, device_id: uuid.UUID, status: DeviceStatus
    ) -> Device:
        device = self.get_by_id(db, device_id=device_id)
        device.status = status
        db.add(device)
        db.commit()
        db.refresh(device)
        return device
    
    
    def decommission(self, db: Session, *, device_id: uuid.UUID) -> Device:
        return self.update_device_status(
            db, device_id=device_id, status=DeviceStatus.DECOMMISSIONED
        )
    
    
    def activate(self, db: Session, *, device_id: uuid.UUID) -> Device:
        return self.update_device_status(
            db, device_id=device_id, status=DeviceStatus.PROVISIONED
        )

    
    def update_cloud_info(
        self, 
        db: Session, 
        *, 
        device_id: uuid.UUID,
        thing_name: str,
        thing_arn: str,
        certificate_id: str,
        certificate_arn: str,
        certificate_path: str,
        private_key_path: str,
        status: DeviceStatus = DeviceStatus.PROVISIONED
    ) -> Device:
        device = self.get_by_id(db, device_id=device_id)
        device.thing_name = thing_name
        device.thing_arn = thing_arn
        device.certificate_id = certificate_id
        device.certificate_arn = certificate_arn
        device.certificate_path = certificate_path
        device.private_key_path = private_key_path
        device.status = status
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

device = CRUDDevice(Device)