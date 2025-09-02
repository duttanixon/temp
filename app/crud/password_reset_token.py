from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.password_reset_token import PasswordResetToken
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import secrets
import uuid

class CRUDPasswordResetToken(CRUDBase[PasswordResetToken, None, None]):
    async def create_token(self, db: AsyncSession, *, user_id: uuid.UUID, expires_in_hours: int = 2) -> PasswordResetToken:
        """Create a new password reset token for a user"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(hours=expires_in_hours)
        
        db_obj = PasswordResetToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_token(self, db: AsyncSession, *, token: str) -> Optional[PasswordResetToken]:
        """Get a valid (unused and not expired) token"""
        result = await db.execute(
            select(PasswordResetToken).filter(
                PasswordResetToken.token == token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.now(ZoneInfo("Asia/Tokyo"))
            )
        )
        return result.scalars().first()
    
    async def mark_as_used(self, db: AsyncSession, *, db_obj: PasswordResetToken) -> PasswordResetToken:
        """Mark a token as used"""
        db_obj.used = True
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def cleanup_expired_tokens(self, db: AsyncSession) -> int:
        """Delete expired tokens (optional cleanup method)"""
        # This will be replaced with an async version of delete later if needed, but this is a start.
        result = await db.execute(
            select(PasswordResetToken).filter(
                PasswordResetToken.expires_at < datetime.now(ZoneInfo("Asia/Tokyo"))
            )
        )
        rows = result.scalars().all()
        for row in rows:
            await db.delete(row)
        await db.commit()
        return len(rows)

password_reset_token = CRUDPasswordResetToken(PasswordResetToken)
