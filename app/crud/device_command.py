from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.device_command import DeviceCommand, CommandStatus
from app.schemas.device_command import DeviceCommandCreate, DeviceCommandUpdate
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo


class CRUDDeviceCommand(
    CRUDBase[DeviceCommand, DeviceCommandCreate, DeviceCommandUpdate]
):
    async def get_by_message_id(
        self, db: AsyncSession, *, message_id: uuid.UUID
    ) -> Optional[DeviceCommand]:
        result = await db.execute(
            select(DeviceCommand)
            .filter(DeviceCommand.message_id == message_id)
        )
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: DeviceCommandCreate) -> DeviceCommand:
        db_obj = DeviceCommand(
            device_id=obj_in.device_id,
            user_id=obj_in.user_id,
            solution_id=obj_in.solution_id,
            command_type=obj_in.command_type,
            status=obj_in.status,
            sent_at=datetime.now(ZoneInfo("Asia/Tokyo")),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_status(
        self,
        db: AsyncSession,
        *,
        message_id: uuid.UUID,
        status: CommandStatus,
        response_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> DeviceCommand:
        """Update command status and response"""
        command = await self.get_by_message_id(db, message_id=message_id)
        if not command:
            return None

        command.status = status
        if response_payload:
            command.response_payload = response_payload
        if error_message:
            command.error_message = error_message
        if status in [
            CommandStatus.SUCCESS,
            CommandStatus.FAILED,
            CommandStatus.TIMEOUT,
        ]:
            command.completed_at = datetime.now(ZoneInfo("Asia/Tokyo"))

        await db.commit()
        await db.refresh(command)
        return command


device_command = CRUDDeviceCommand(DeviceCommand)
