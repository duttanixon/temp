# app/crud/crud_ai_model.py
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.crud.base import CRUDBase
from app.models.ai_model import AIModel, AIModelStatus
from app.schemas.ai_model import AIModelCreate, AIModelUpdate
from app.utils.logger import get_logger
from datetime import datetime
from zoneinfo import ZoneInfo

logger = get_logger("crud.ai_model")


class CRUDAIModel(CRUDBase[AIModel, AIModelCreate, AIModelUpdate]):
    """CRUD operations for AI Model"""
    
    def get_by_id(
        self, db: Session, *, model_id: uuid.UUID
    ) -> Optional[AIModel]:
        """Get AI model by ID"""
        return db.query(AIModel).filter(AIModel.model_id == model_id).first()

    def get_by_name_and_version(
        self, db: Session, *, name: str, version: str
    ) -> Optional[AIModel]:
        """Get AI model by name and version combination"""
        return db.query(AIModel).filter(
            and_(
                AIModel.name == name,
                AIModel.version == version
            )
        ).first()

    def get_multi_with_filters(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[AIModelStatus] = None,
        name: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[AIModel]:
        """
        Get multiple AI models with optional filters and sorting
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by model status
            name: Filter by model name (partial match)
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
        """
        query = db.query(AIModel)
        
        # Apply filters
        if status:
            query = query.filter(AIModel.status == status)
        
        if name:
            query = query.filter(AIModel.name.ilike(f"%{name}%"))
        
        # Apply sorting
        sort_column = getattr(AIModel, sort_by, AIModel.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        return query.offset(skip).limit(limit).all()

    def count_with_filters(
        self,
        db: Session,
        *,
        status: Optional[AIModelStatus] = None,
        name: Optional[str] = None
    ) -> int:
        """Count models with optional filters"""
        query = db.query(func.count(AIModel.model_id))
        
        if status:
            query = query.filter(AIModel.status == status)
        
        if name:
            query = query.filter(AIModel.name.ilike(f"%{name}%"))
        
        return query.scalar()

    def get_active_models(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[AIModel]:
        """Get all active AI models"""
        return self.get_multi_with_filters(
            db, skip=skip, limit=limit, status=AIModelStatus.ACTIVE
        )

    def get_by_s3_key(
        self, db: Session, *, s3_key: str
    ) -> Optional[AIModel]:
        """Get AI model by S3 key"""
        return db.query(AIModel).filter(AIModel.s3_key == s3_key).first()

    def create_with_s3_info(
        self,
        db: Session,
        *,
        obj_in: AIModelCreate,
        s3_bucket: str,
        s3_key: str
    ) -> AIModel:
        """
        Create AI model with S3 information
        
        Args:
            db: Database session
            obj_in: Model creation data
            s3_bucket: S3 bucket name
            s3_key: S3 object key
        """
        db_obj = AIModel(
            name=obj_in.name,
            version=obj_in.version,
            description=obj_in.description,
            status=obj_in.status or AIModelStatus.ACTIVE,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            created_at=datetime.now(ZoneInfo("Asia/Tokyo")),
            updated_at=datetime.now(ZoneInfo("Asia/Tokyo"))
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Created AI model: {db_obj.model_id} - {db_obj.name} v{db_obj.version}")
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: AIModel,
        obj_in: AIModelUpdate
    ) -> AIModel:
        """Update AI model"""
        update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.now(ZoneInfo("Asia/Tokyo"))
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Updated AI model: {db_obj.model_id}")
        return db_obj

    def update_status(
        self,
        db: Session,
        *,
        model_id: uuid.UUID,
        status: AIModelStatus
    ) -> Optional[AIModel]:
        """Update AI model status"""
        db_obj = self.get_by_id(db, model_id=model_id)
        if db_obj:
            db_obj.status = status
            db_obj.updated_at = datetime.now(ZoneInfo("Asia/Tokyo"))
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated AI model {model_id} status to {status}")
        return db_obj

    def deprecate_model(
        self, db: Session, *, model_id: uuid.UUID
    ) -> Optional[AIModel]:
        """Deprecate an AI model"""
        return self.update_status(db, model_id=model_id, status=AIModelStatus.DEPRECATED)

    def activate_model(
        self, db: Session, *, model_id: uuid.UUID
    ) -> Optional[AIModel]:
        """Activate an AI model"""
        return self.update_status(db, model_id=model_id, status=AIModelStatus.ACTIVE)

    def count_by_status(
        self, db: Session, *, status: AIModelStatus
    ) -> int:
        """Count models by status"""
        return db.query(AIModel).filter(AIModel.status == status).count()

    def get_latest_version(
        self, db: Session, *, name: str
    ) -> Optional[AIModel]:
        """Get the latest version of a model by name"""
        return db.query(AIModel).filter(
            AIModel.name == name
        ).order_by(AIModel.created_at.desc()).first()

    def get_all_versions(
        self, db: Session, *, name: str
    ) -> List[AIModel]:
        """Get all versions of a model by name"""
        return db.query(AIModel).filter(
            AIModel.name == name
        ).order_by(AIModel.version.desc()).all()

    def search_models(
        self,
        db: Session,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AIModel]:
        """
        Search models by name or description
        
        Args:
            db: Database session
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
        """
        search_pattern = f"%{search_term}%"
        return db.query(AIModel).filter(
            or_(
                AIModel.name.ilike(search_pattern),
                AIModel.description.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()

    def delete_hard(
        self, db: Session, *, model_id: uuid.UUID
    ) -> Optional[AIModel]:
        """
        Permanently delete an AI model (use with caution)
        This should only be used for cleanup of failed uploads
        """
        db_obj = self.get_by_id(db, model_id=model_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            logger.warning(f"Hard deleted AI model: {model_id}")
        return db_obj

    def get_models_by_date_range(
        self,
        db: Session,
        *,
        start_date: datetime,
        end_date: datetime
    ) -> List[AIModel]:
        """Get models created within a date range"""
        return db.query(AIModel).filter(
            and_(
                AIModel.created_at >= start_date,
                AIModel.created_at <= end_date
            )
        ).order_by(AIModel.created_at.desc()).all()


# Create instance
ai_model = CRUDAIModel(AIModel)