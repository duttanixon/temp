import uuid
from sqlalchemy import Column, String, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base, jst_now


class SolutionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    BETA = "BETA"
    DEPRECATED = "DEPRECATED"

class Solution(Base):
    __tablename__ = "solutions"
    
    solution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    version = Column(String, nullable=True)
    compatibility = Column(JSON, nullable=False)  # Array of compatible device types
    configuration_template = Column(JSON, nullable=True) # Common configuration accoss all devies running the solution
    status = Column(Enum(SolutionStatus), nullable=False, default=SolutionStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=jst_now)
    updated_at = Column(DateTime(timezone=True), default=jst_now, onupdate=jst_now)
    
    # Relationships
    customer_solutions = relationship("CustomerSolution", back_populates="solution")
    device_solutions = relationship("DeviceSolution", back_populates="solution")
    packages = relationship("SolutionPackage", back_populates="solution")