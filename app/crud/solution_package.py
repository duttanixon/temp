# app/crud/solution_package.py
from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.crud.base import CRUDBase
from app.models.solution_package import SolutionPackage
from app.models.solution_package_model import SolutionPackageModel
from app.schemas.solution_package import SolutionPackageCreate, SolutionPackageUpdate
import uuid
from datetime import datetime

class CRUDSolutionPackage(CRUDBase[SolutionPackage, SolutionPackageCreate, SolutionPackageUpdate]):
    
    def get_by_id(self, db: Session, *, package_id: uuid.UUID) -> Optional[SolutionPackage]:
        """Get package by ID"""
        return db.query(SolutionPackage).filter(
            SolutionPackage.package_id == package_id
        ).first()
    
    def get_by_name_and_version(
        self, db: Session, *, name: str, version: str, solution_id: uuid.UUID
    ) -> Optional[SolutionPackage]:
        """Get package by name, version and solution"""
        return db.query(SolutionPackage).filter(
            SolutionPackage.name == name,
            SolutionPackage.version == version,
            SolutionPackage.solution_id == solution_id
        ).first()
    
    def get_by_solution(
        self, db: Session, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[SolutionPackage]:
        """Get all packages for a solution"""
        return db.query(SolutionPackage).filter(
            SolutionPackage.solution_id == solution_id
        ).order_by(desc(SolutionPackage.created_at)).offset(skip).limit(limit).all()
    
    def get_latest_by_solution(
        self, db: Session, *, solution_id: uuid.UUID
    ) -> Optional[SolutionPackage]:
        """Get the latest package for a solution"""
        return db.query(SolutionPackage).filter(
            SolutionPackage.solution_id == solution_id
        ).order_by(desc(SolutionPackage.created_at)).first()
    
    def create_with_s3_info(
        self, db: Session, *, obj_in: SolutionPackageCreate, s3_bucket: str, s3_key: str
    ) -> SolutionPackage:
        """Create package with S3 information"""
        db_obj = SolutionPackage(
            solution_id=obj_in.solution_id,
            name=obj_in.name,
            version=obj_in.version,
            description=obj_in.description,
            s3_bucket=s3_bucket,
            s3_key=s3_key
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_multi_with_filters(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        solution_id: Optional[uuid.UUID] = None,
        name: Optional[str] = None,
        version: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[SolutionPackage], int]:
        """Get packages with filters"""
        query = db.query(SolutionPackage)
        
        # Apply filters
        if solution_id:
            query = query.filter(SolutionPackage.solution_id == solution_id)
        if name:
            query = query.filter(SolutionPackage.name.ilike(f"%{name}%"))
        if version:
            query = query.filter(SolutionPackage.version.ilike(f"%{version}%"))
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(SolutionPackage, sort_by, SolutionPackage.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        packages = query.offset(skip).limit(limit).all()
        
        return packages, total
    
    def associate_with_model(
        self, db: Session, *, package_id: uuid.UUID, model_id: uuid.UUID
    ) -> SolutionPackageModel:
        """Associate a package with an AI model"""
        association = SolutionPackageModel(
            package_id=package_id,
            model_id=model_id
        )
        db.add(association)
        db.commit()
        db.refresh(association)
        return association
    
    def get_model_associations(
        self, db: Session, *, package_id: uuid.UUID
    ) -> List[SolutionPackageModel]:
        """Get all model associations for a package"""
        return db.query(SolutionPackageModel).filter(
            SolutionPackageModel.package_id == package_id
        ).all()
    
    def remove_model_association(
        self, db: Session, *, package_id: uuid.UUID, model_id: uuid.UUID
    ) -> bool:
        """Remove a model association from a package"""
        association = db.query(SolutionPackageModel).filter(
            SolutionPackageModel.package_id == package_id,
            SolutionPackageModel.model_id == model_id
        ).first()
        
        if association:
            db.delete(association)
            db.commit()
            return True
        return False
    
    def get_packages_with_model(
        self, db: Session, *, model_id: uuid.UUID
    ) -> List[SolutionPackage]:
        """Get all packages that include a specific AI model"""
        package_ids = db.query(SolutionPackageModel.package_id).filter(
            SolutionPackageModel.model_id == model_id
        ).subquery()
        
        return db.query(SolutionPackage).filter(
            SolutionPackage.package_id.in_(package_ids)
        ).all()
    
    def update_package_status(
        self, db: Session, *, package_id: uuid.UUID, status: str
    ) -> Optional[SolutionPackage]:
        """Update package status"""
        package = self.get_by_id(db, package_id=package_id)
        if package:
            package.status = status
            package.updated_at = datetime.now()
            db.commit()
            db.refresh(package)
        return package
    
    def delete_package(
        self, db: Session, *, package_id: uuid.UUID
    ) -> bool:
        """Delete a package and its associations"""
        package = self.get_by_id(db, package_id=package_id)
        if not package:
            return False
        
        # Delete model associations first
        db.query(SolutionPackageModel).filter(
            SolutionPackageModel.package_id == package_id
        ).delete()
        
        # Delete the package
        db.delete(package)
        db.commit()
        return True


solution_package = CRUDSolutionPackage(SolutionPackage)