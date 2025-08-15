from sqlalchemy import Column, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class SolutionPackageModel(Base):
    __tablename__ = "solution_package_models"
    
    package_id = Column(UUID(as_uuid=True), ForeignKey("solution_package.package_id"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ai_models.model_id"), nullable=False)
    
    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('package_id', 'model_id'),
    )
    
    # Relationships
    package = relationship("SolutionPackage", back_populates="package_associations")
    ai_model = relationship("AIModel", back_populates="package_associations")
