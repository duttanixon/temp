import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base, jst_now


class AIModelStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    IN_TESTING = "IN_TESTING"


class AIModel(Base):
    __tablename__ = "ai_models"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(AIModelStatus), nullable=False, default=AIModelStatus.ACTIVE)
    s3_bucket = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)
    
    # Relationships
    package_associations = relationship("SolutionPackageModel", back_populates="ai_model")
