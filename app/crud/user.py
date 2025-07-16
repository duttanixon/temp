from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserCreateWithoutPassword
import uuid


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, db: Session, *, user_id: uuid.UUID) -> Optional[User]:
        return db.query(User).filter(User.user_id == user_id).first()
    
    def get_by_customer(self, db: Session, *, customer_id: uuid.UUID) -> List[User]:
        return db.query(User).filter(User.customer_id == customer_id).all()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            password_hash=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            role=obj_in.role,
            customer_id=obj_in.customer_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.status == UserStatus.ACTIVE
    
    def is_admin(self, user: User) -> bool:
        return user.role == "admin"
    
    def suspend(self, db: Session, *, user_id: uuid.UUID) -> User:
        user = self.get_by_id(db, user_id=user_id)
        user.status = UserStatus.SUSPENDED
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def activate(self, db: Session, *, user_id: uuid.UUID) -> User:
        user = self.get_by_id(db, user_id=user_id)
        user.status = UserStatus.ACTIVE
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def create_without_password(self, db: Session, *, obj_in: UserCreateWithoutPassword) -> User:
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
        db.commit()
        db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)