from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, and_, select, delete, func
from app.crud.base import CRUDBase
from app.models import Device, DeviceStatus, Customer, DeviceSolution, Solution, Job, DeviceCommand, CityEyeHumanTable as HumanTable, CityEyeTrafficTable as TrafficTable
from app.schemas.device import DeviceCreate, DeviceUpdate
import uuid

class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    async def get_by_id(self, db: AsyncSession, *, device_id: uuid.UUID) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.device_id == device_id))
        return result.scalars().first()
    
    async def get_by_mac_address(self, db: AsyncSession, *, mac_address: str) -> Optional[Device]:
        if not mac_address:
            return None
        result = await db.execute(select(Device).filter(Device.mac_address == mac_address))
        return result.scalars().first()
    
    async def get_by_thing_name(self, db: AsyncSession, *, thing_name: str) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.thing_name == thing_name))
        return result.scalars().first()

    async def get_by_device_name(self, db: AsyncSession, *, device_name: str) -> Optional[Device]:
        result = await db.execute(select(Device).filter(Device.name == device_name))
        return result.scalars().first()

    async def get_by_customer(
        self, db: AsyncSession, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        result = await db.execute(
            select(Device)
            .filter(Device.customer_id == customer_id)
            .order_by(desc(Device.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_customer_name_and_solution_filter(
        self, db: AsyncSession, *, solution_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100
    ) -> List[Device]:
        """Get all devices with customer name, optionally filtered by solution"""
        query = (
            select(
                Device,
                Customer.name.label("customer_name"),
                Solution.name.label("solution_name"),
                Job.job_type.label("latest_job_type"),
                Job.status.label("latest_job_status"),
            )
            .join(Customer, Device.customer_id == Customer.customer_id)
            .outerjoin(DeviceSolution, and_(Device.device_id == DeviceSolution.device_id))
            .outerjoin(Solution, DeviceSolution.solution_id == Solution.solution_id)
            .outerjoin(Job, Device.latest_job_id == Job.id)
        )
        
        if solution_id:
            query = query.filter(DeviceSolution.solution_id == solution_id)
        
        query = query.order_by(
            Device.customer_id, 
            desc(Device.created_at)
        ).offset(skip).limit(limit)
        
        results = (await db.execute(query)).all()
        
        processed_devices = []
        for row in results:
            device_obj, customer_name, solution_name, latest_job_type, latest_job_status = row
            setattr(device_obj, "customer_name", customer_name)
            setattr(device_obj, "solution_name", solution_name)
            setattr(device_obj, "latest_job_type", latest_job_type)
            setattr(device_obj, "latest_job_status", latest_job_status)
            processed_devices.append(device_obj)

        return processed_devices

    async def get_by_customer_with_name_and_solution_filter(
        self, db: AsyncSession, *, customer_id: uuid.UUID, solution_id: Optional[uuid.UUID] = None,
        skip: int = 0, limit: int = 100
    ) -> List[Device]:
        """Get a customer's devices with solution and latest job info."""
        query = (
            select(
                Device,
                Customer.name.label("customer_name"),
                Solution.name.label("solution_name"),
                Job.job_type.label("latest_job_type"),
                Job.status.label("latest_job_status"),
            )
            .join(Customer, Device.customer_id == Customer.customer_id)
            .outerjoin(DeviceSolution, and_(Device.device_id == DeviceSolution.device_id))
            .outerjoin(Solution, DeviceSolution.solution_id == Solution.solution_id)
            .outerjoin(Job, Device.latest_job_id == Job.id)
            .filter(Device.customer_id == customer_id)
        )

        if solution_id:
            query = query.filter(DeviceSolution.solution_id == solution_id)

        query = query.order_by(desc(Device.created_at)).offset(skip).limit(limit)

        results = (await db.execute(query)).all()

        processed_devices = []
        for row in results:
            device_obj, customer_name, solution_name, latest_job_type, latest_job_status = row
            setattr(device_obj, "customer_name", customer_name)
            setattr(device_obj, "solution_name", solution_name)
            setattr(device_obj, "latest_job_type", latest_job_type)
            setattr(device_obj, "latest_job_status", latest_job_status)
            processed_devices.append(device_obj)

        return processed_devices


    async def create(self, db: AsyncSession, *, obj_in: DeviceCreate, device_name: str) -> Device:
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
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def update_device_status(
        self, db: AsyncSession, *, device_id: uuid.UUID, status: DeviceStatus
    ) -> Device:
        device = await self.get_by_id(db, device_id=device_id)
        if device:
            device.status = status
            db.add(device)
            await db.commit()
            await db.refresh(device)
        return device
    
    
    async def decommission(self, db: AsyncSession, *, device_id: uuid.UUID) -> Device:
        device = await self.get_by_id(db, device_id=device_id)
        device.thing_name = None
        device.thing_arn = None
        device.certificate_id = None
        device.certificate_arn = None
        device.certificate_path = None
        device.private_key_path = None
        device.status = DeviceStatus.DECOMMISSIONED
        db.add(device)
        await db.commit()
        await db.refresh(device)
        return device
    
    
    async def activate(self, db: AsyncSession, *, device_id: uuid.UUID) -> Device:
        return await self.update_device_status(
            db, device_id=device_id, status=DeviceStatus.ACTIVE
        )

    async def provision(self, db: AsyncSession, *, device_id: uuid.UUID) -> Device:
        return await self.update_device_status(
            db, device_id=device_id, status=DeviceStatus.PROVISIONED
        )

    async def update_cloud_info(
        self, 
        db: AsyncSession, 
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
        device = await self.get_by_id(db, device_id=device_id)
        if device:
            device.thing_name = thing_name
            device.thing_arn = thing_arn
            device.certificate_id = certificate_id
            device.certificate_arn = certificate_arn
            device.certificate_path = certificate_path
            device.private_key_path = private_key_path
            device.status = status
            db.add(device)
            await db.commit()
            await db.refresh(device)
        return device

    async def create_with_cloud_info(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: Dict[str, Any], 
        device_name: str
    ) -> Device:
        """Create a device with cloud provisioning information in one operation"""
        db_obj = Device(
            name=device_name,
            description=obj_in.get('description'),
            mac_address=obj_in.get('mac_address'),
            serial_number=obj_in.get('serial_number'),
            device_type=obj_in['device_type'],
            firmware_version=obj_in.get('firmware_version'),
            ip_address=obj_in.get('ip_address'),
            location=obj_in.get('location'),
            customer_id=obj_in['customer_id'],
            configuration=obj_in.get('configuration'),
            latitude=obj_in.get('latitude'),
            longitude=obj_in.get('longitude'),
            # Cloud info
            thing_name=obj_in.get('thing_name'),
            thing_arn=obj_in.get('thing_arn'),
            certificate_id=obj_in.get('certificate_id'),
            certificate_arn=obj_in.get('certificate_arn'),
            certificate_path=obj_in.get('certificate_url'),  # Note: mapping certificate_url to certificate_path
            private_key_path=obj_in.get('private_key_url'),  # Note: mapping private_key_url to private_key_path
            status=obj_in.get('status', DeviceStatus.PROVISIONED)
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_with_customer_name_and_solution(
        self,
        db: AsyncSession,
        *,
        device_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        # Query the device with customer information
        query = (
            select(Device, Customer.name.label("customer_name"))
            .join(Customer, Customer.customer_id == Device.customer_id)
            .filter(Device.device_id == device_id)
        )
        result = await db.execute(query)
        result_row = result.first()
        
        if not result_row:
            return None
            
        device_obj, customer_name = result_row
        
        # Convert to dict and add customer name
        device_dict = {
            **device_obj.__dict__,
            "customer_name": customer_name,
        }
        
        # Get associated solutions
        solution_result = await db.execute(
            select(
                DeviceSolution.solution_id,
                Solution.name.label("solution_name")
            )
            .join(Solution, Solution.solution_id == DeviceSolution.solution_id)
            .filter(DeviceSolution.device_id == device_id)
        )
        solution_row = solution_result.first()
        
        # Add solutions information
        device_dict["solution_name"] = solution_row.solution_name if solution_row else None
        
        return device_dict

    async def cascade_delete(self, db: AsyncSession, *, device_id: uuid.UUID) -> Device:
        """
        Delete a device and all its related records in the correct order to avoid foreign key violations.
        """
        # Get the device first to return it after deletion
        device_obj = await self.get_by_id(db, device_id=device_id)
        if not device_obj:
            raise ValueError(f"Device with ID {device_id} not found")
        
        try:
            # 1. Delete City Eye data (human and traffic tables)
            await db.execute(delete(HumanTable).where(HumanTable.device_id == device_id))
            await db.execute(delete(TrafficTable).where(TrafficTable.device_id == device_id))
            
            # 2. Delete device commands
            await db.execute(delete(DeviceCommand).where(DeviceCommand.device_id == device_id))
            
            # 3. Delete jobs related to this device
            await db.execute(delete(Job).where(Job.device_id == device_id))
            
            # 4. Delete device solutions
            await db.execute(delete(DeviceSolution).where(DeviceSolution.device_id == device_id))
            
            # 5. Finally, delete the device itself
            await db.delete(device_obj)
            
            # Commit all deletions
            await db.commit()
            
            return device_obj
            
        except Exception as e:
            # Rollback on any error
            await db.rollback()
            raise e

    async def safe_delete_check(self, db: AsyncSession, *, device_id: uuid.UUID) -> Dict[str, int]:
        """
        Check what related records would be deleted before performing cascade delete.
        Returns counts of related records.
        """
        counts = {}
        
        # Count related records
        result = await db.execute(select(func.count()).select_from(DeviceSolution).where(DeviceSolution.device_id == device_id))
        counts['device_solutions'] = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(Job).where(Job.device_id == device_id))
        counts['jobs'] = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(DeviceCommand).where(DeviceCommand.device_id == device_id))
        counts['device_commands'] = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(HumanTable).where(HumanTable.device_id == device_id))
        counts['human_data_records'] = result.scalar()
        
        result = await db.execute(select(func.count()).select_from(TrafficTable).where(TrafficTable.device_id == device_id))
        counts['traffic_data_records'] = result.scalar()
        
        return counts

device = CRUDDevice(Device)
