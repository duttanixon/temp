from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.crud.base import CRUDBase
from app.models import Device, DeviceStatus, Customer, DeviceSolution, Solution, Job, DeviceSolutionStatus
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

    def get_by_device_name(self, db: Session, *, device_name: str) -> Optional[Device]:
        return db.query(Device).filter(Device.name == device_name).first()

    def get_by_customer(
        self, db: Session, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        return db.query(Device).filter(
            Device.customer_id == customer_id
        ).order_by(desc(Device.created_at)).offset(skip).limit(limit).all()

    def get_with_customer_name_and_solution_filter(
        self, db: Session, *, solution_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        """Get all devices with customer name, optionally filtered by solution"""
        query = (
            db.query(
                Device,
                Customer.name.label("customer_name"),
                Solution.name.label("solution_name"),
                Solution.version.label("solution_version"),
                Job.job_type.label("latest_job_type"),
                Job.status.label("latest_job_status"),
            )
            .join(Customer, Device.customer_id == Customer.customer_id)
            .outerjoin(DeviceSolution, and_(Device.device_id == DeviceSolution.device_id, DeviceSolution.status == DeviceSolutionStatus.ACTIVE))
            .outerjoin(Solution, DeviceSolution.solution_id == Solution.solution_id)
            .outerjoin(Job, Device.latest_job_id == Job.id)
        )
        
        if solution_id:
            query = query.filter(DeviceSolution.solution_id == solution_id)
        
        query = query.order_by(
            Device.customer_id, 
            desc(Device.created_at)
        ).offset(skip).limit(limit)
        
        results = query.all()
        
        processed_devices = []
        for row in results:
            device, customer_name, solution_name, solution_version, latest_job_type, latest_job_status = row
            setattr(device, "customer_name", customer_name)
            setattr(device, "solution_name", solution_name)
            setattr(device, "solution_version", solution_version)
            setattr(device, "latest_job_type", latest_job_type)
            setattr(device, "latest_job_status", latest_job_status)
            processed_devices.append(device)

        return processed_devices

    def get_by_customer_with_name_and_solution_filter(
        self, db: Session, *, customer_id: uuid.UUID, solution_id: Optional[uuid.UUID] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Device]:
        """Get a customer's devices with solution and latest job info."""
        query = (
            db.query(
                Device,
                Customer.name.label("customer_name"),
                Solution.name.label("solution_name"),
                Solution.version.label("solution_version"),
                Job.job_type.label("latest_job_type"),
                Job.status.label("latest_job_status"),
            )
            .join(Customer, Device.customer_id == Customer.customer_id)
            .outerjoin(DeviceSolution, and_(Device.device_id == DeviceSolution.device_id, DeviceSolution.status == DeviceSolutionStatus.ACTIVE))
            .outerjoin(Solution, DeviceSolution.solution_id == Solution.solution_id)
            .outerjoin(Job, Device.latest_job_id == Job.id)
            .filter(Device.customer_id == customer_id)
        )

        if solution_id:
            query = query.filter(DeviceSolution.solution_id == solution_id)

        query = query.order_by(desc(Device.created_at)).offset(skip).limit(limit)

        results = query.all()

        processed_devices = []
        for row in results:
            device, customer_name, solution_name, solution_version, latest_job_type, latest_job_status = row
            setattr(device, "customer_name", customer_name)
            setattr(device, "solution_name", solution_name)
            setattr(device, "solution_version", solution_version)
            setattr(device, "latest_job_type", latest_job_type)
            setattr(device, "latest_job_status", latest_job_status)
            processed_devices.append(device)

        return processed_devices


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
            latitude=obj_in.latitude,
            longitude=obj_in.longitude
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