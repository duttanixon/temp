import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base, jst_now


class SolutionPackage(Base):
    __tablename__ = "solution_package"
    
    package_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    s3_bucket = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)
    
    # Relationships
    solution = relationship("Solution", back_populates="packages")
    package_associations = relationship("SolutionPackageModel", back_populates="package")
    device_solutions = relationship("DeviceSolution", back_populates="package")
