from typing import Optional
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models.password_reset_token import PasswordResetToken
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import secrets
import uuid

class CRUDPasswordResetToken(CRUDBase[PasswordResetToken, None, None]):
    def create_token(self, db: Session, *, user_id: uuid.UUID, expires_in_hours: int = 2) -> PasswordResetToken:
        """Create a new password reset token for a user"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(hours=expires_in_hours)
        
        db_obj = PasswordResetToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_token(self, db: Session, *, token: str) -> Optional[PasswordResetToken]:
        """Get a valid (unused and not expired) token"""
        return db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.now(ZoneInfo("Asia/Tokyo"))
        ).first()
    
    def mark_as_used(self, db: Session, *, db_obj: PasswordResetToken) -> PasswordResetToken:
        """Mark a token as used"""
        db_obj.used = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """Delete expired tokens (optional cleanup method)"""
        result = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < datetime.now(ZoneInfo("Asia/Tokyo"))
        ).delete()
        db.commit()
        return result

password_reset_token = CRUDPasswordResetToken(PasswordResetToken)