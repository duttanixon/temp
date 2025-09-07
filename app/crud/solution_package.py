from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, func, delete
from sqlalchemy.orm import joinedload, selectinload
from app.crud.base import CRUDBase
from app.models.solution_package import SolutionPackage
from app.models.solution_package_model import SolutionPackageModel
from app.schemas.solution_package import SolutionPackageCreate, SolutionPackageUpdate
import uuid
import re
from datetime import datetime

class CRUDSolutionPackage(CRUDBase[SolutionPackage, SolutionPackageCreate, SolutionPackageUpdate]):
    
    async def get_by_id(self, db: AsyncSession, *, package_id: uuid.UUID) -> Optional[SolutionPackage]:
        """Get package by ID"""
        result = await db.execute(
            select(SolutionPackage).filter(SolutionPackage.package_id == package_id)
        )
        return result.scalars().first()
    
    async def get_by_name_and_version(
        self, db: AsyncSession, *, name: str, version: str, solution_id: uuid.UUID
    ) -> Optional[SolutionPackage]:
        """Get package by name, version and solution"""
        result = await db.execute(
            select(SolutionPackage).filter(
                SolutionPackage.name == name,
                SolutionPackage.version == version,
                SolutionPackage.solution_id == solution_id
            )
        )
        return result.scalars().first()

    async def get_latest_by_name_and_solution(self, db: AsyncSession, *, name: str, solution_id: uuid.UUID) -> Optional[SolutionPackage]:
        """
        Get the latest version of a specific package by name and solution ID based on semantic versioning.
        """
        result = await db.execute(
            select(SolutionPackage).filter(
                SolutionPackage.name == name,
                SolutionPackage.solution_id == solution_id
            )
        )
        packages = list(result.scalars().all())

        if not packages:
            return None

        # Custom logic to find the latest version based on semantic versioning
        def parse_version(version_str):
            # Extract major, minor, patch numbers from the version string
            match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                return [int(x) for x in match.groups()]
            return [0, 0, 0]

        latest_package = max(packages, key=lambda p: parse_version(p.version))
        return latest_package
    
    async def get_by_solution(
        self, db: AsyncSession, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[SolutionPackage]:
        """Get all packages for a solution"""
        result = await db.execute(
            select(SolutionPackage).filter(
                SolutionPackage.solution_id == solution_id
            ).order_by(desc(SolutionPackage.created_at)).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest_by_solution(
        self, db: AsyncSession, *, solution_id: uuid.UUID
    ) -> Optional[SolutionPackage]:
        """Get the latest package for a solution"""
        result = await db.execute(
            select(SolutionPackage).filter(
                SolutionPackage.solution_id == solution_id
            ).order_by(desc(SolutionPackage.created_at)).limit(1)
        )
        return result.scalars().first()
    
    async def create_with_s3_info(
        self, db: AsyncSession, *, obj_in: SolutionPackageCreate, s3_bucket: str, s3_key: str
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
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_with_details(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        solution_id: Optional[uuid.UUID] = None,
        name: Optional[str] = None,
        version: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[SolutionPackage], int]:
        """
        Get packages with filters and eager-loaded relationships.
        This function solves the N+1 query problem by joining necessary tables upfront.
        """
        query = select(SolutionPackage).options(
            joinedload(SolutionPackage.solution),
            selectinload(SolutionPackage.package_associations).joinedload(SolutionPackageModel.ai_model)
        )
        
        # Apply filters
        if solution_id:
            query = query.filter(SolutionPackage.solution_id == solution_id)
        if name:
            query = query.filter(SolutionPackage.name.ilike(f"%{name}%"))
        if version:
            query = query.filter(SolutionPackage.version.ilike(f"%{version}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()
        
        # Apply sorting
        sort_column = getattr(SolutionPackage, sort_by, SolutionPackage.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Apply pagination
        result = await db.execute(query.offset(skip).limit(limit))
        packages = list(result.scalars().all())
        
        return packages, total
    
    async def associate_with_model(
        self, db: AsyncSession, *, package_id: uuid.UUID, model_id: uuid.UUID
    ) -> SolutionPackageModel:
        """Associate a package with an AI model"""
        association = SolutionPackageModel(
            package_id=package_id,
            model_id=model_id
        )
        db.add(association)
        await db.commit()
        await db.refresh(association)
        return association
    
    async def get_model_associations(
        self, db: AsyncSession, *, package_id: uuid.UUID
    ) -> List[SolutionPackageModel]:
        """Get all model associations for a package"""
        result = await db.execute(
            select(SolutionPackageModel).filter(SolutionPackageModel.package_id == package_id)
        )
        return list(result.scalars().all())
    
    async def remove_model_association(
        self, db: AsyncSession, *, package_id: uuid.UUID, model_id: uuid.UUID
    ) -> bool:
        """Remove a model association from a package"""
        association_to_delete = await db.get(SolutionPackageModel, (package_id, model_id))
        
        if association_to_delete:
            await db.delete(association_to_delete)
            await db.commit()
            return True
        return False
    
    async def get_packages_with_model(
        self, db: AsyncSession, *, model_id: uuid.UUID
    ) -> List[SolutionPackage]:
        """Get all packages that include a specific AI model"""
        query = select(SolutionPackage).join(SolutionPackageModel).filter(SolutionPackageModel.model_id == model_id)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def update_package_status(
        self, db: AsyncSession, *, package_id: uuid.UUID, status: str
    ) -> Optional[SolutionPackage]:
        """Update package status"""
        package = await self.get_by_id(db, package_id=package_id)
        if package:
            package.status = status
            package.updated_at = datetime.now()
            await db.commit()
            await db.refresh(package)
        return package
    
    async def delete_package(
        self, db: AsyncSession, *, package_id: uuid.UUID
    ) -> bool:
        """Delete a package and its associations"""
        package = await self.get_by_id(db, package_id=package_id)
        if not package:
            return False
        
        # Delete model associations first
        await db.execute(
            delete(SolutionPackageModel).filter(SolutionPackageModel.package_id == package_id)
        )
        
        # Delete the package
        await db.delete(package)
        await db.commit()
        return True


solution_package = CRUDSolutionPackage(SolutionPackage)