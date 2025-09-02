from typing import Any, Dict, Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserCreateWithoutPassword
import uuid


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    
    async def get_by_id(self, db: AsyncSession, *, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(select(User).filter(User.user_id == user_id))
        return result.scalars().first()
    
    async def get_by_customer(self, db: AsyncSession, *, customer_id: uuid.UUID) -> List[User]:
        result = await db.execute(select(User).filter(User.customer_id == customer_id))
        return list(result.scalars().all())
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            password_hash=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            role=obj_in.role,
            customer_id=obj_in.customer_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_password
        return await super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.status == UserStatus.ACTIVE
    
    def is_admin(self, user: User) -> bool:
        return user.role == "admin"
    
    async def suspend(self, db: AsyncSession, *, user_id: uuid.UUID) -> User:
        user = await self.get_by_id(db, user_id=user_id)
        user.status = UserStatus.SUSPENDED
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def activate(self, db: AsyncSession, *, user_id: uuid.UUID) -> User:
        user = await self.get_by_id(db, user_id=user_id)
        user.status = UserStatus.ACTIVE
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def create_without_password(self, db: AsyncSession, *, obj_in: UserCreateWithoutPassword) -> User:
        """Create a user without setting a password (they will set it via email link)"""
        # Generate a temporary random password that will never be used
        temp_password = str(uuid.uuid4())
        
        db_obj = User(
            user_id=uuid.uuid4(),
            email=obj_in.email,
            password_hash=get_password_hash(temp_password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            role=obj_in.role,
            customer_id=obj_in.customer_id,
            status=UserStatus.ACTIVE
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
