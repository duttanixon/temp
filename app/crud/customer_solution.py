from typing import Any, Dict, Optional, Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.crud.base import CRUDBase
from app.models import CustomerSolution, LicenseStatus, DeviceSolution, Device, Solution, Customer
from app.schemas.customer_solution import CustomerSolutionCreate, CustomerSolutionUpdate
import uuid
from datetime import date

class CRUDCustomerSolution(CRUDBase[CustomerSolution, CustomerSolutionCreate, CustomerSolutionUpdate]):
    async def get_by_id(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[CustomerSolution]:
        result = await db.execute(select(CustomerSolution).filter(CustomerSolution.id == id))
        return result.scalars().first()

    async def get_by_customer_and_solution(
        self, db: AsyncSession, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> Optional[CustomerSolution]:
        result = await db.execute(
            select(CustomerSolution).filter(
                CustomerSolution.customer_id == customer_id,
                CustomerSolution.solution_id == solution_id
            )
        )
        return result.scalars().first()

    async def get_by_customer_and_solution_enhanced(
        self, db: AsyncSession, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> Optional[Dict]:
        # First get the customer solution record
        cs = await self.get_by_customer_and_solution(db, customer_id=customer_id, solution_id=solution_id)

        # If no customer solution record is found, return None
        if not cs:
            return None

        # Get the solution details
        sol = await db.execute(select(Solution).filter(Solution.solution_id == solution_id))
        sol_obj = sol.scalars().first()
        
        # Combine data
        result = cs.__dict__.copy()
        if sol_obj:
            result["solution_name"] = sol_obj.name
            
        devices_count_result = await db.execute(
            select(func.count(DeviceSolution.id))
            .join(Device, DeviceSolution.device_id == Device.device_id)
            .filter(
                Device.customer_id == customer_id,
                DeviceSolution.solution_id == solution_id
            )
        )
        devices_count = devices_count_result.scalar()
        
        result["devices_count"] = devices_count
        return result
    
    async def get_by_customer(
        self, db: AsyncSession, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[CustomerSolution]:
        result = await db.execute(
            select(CustomerSolution)
            .filter(CustomerSolution.customer_id == customer_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_solution(self, db: AsyncSession, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[CustomerSolution]:
        """Get customer solutions for a specific solution"""
        result = await db.execute(
            select(CustomerSolution)
            .filter(CustomerSolution.solution_id == solution_id)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())


    async def get_by_active_solution(self, db: AsyncSession, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[CustomerSolution]:
        """Get customer solutions for a specific solution"""
        result = await db.execute(
            select(CustomerSolution)
            .filter(CustomerSolution.solution_id == solution_id)
            .filter(CustomerSolution.license_status == LicenseStatus.ACTIVE)
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_customer(
        self, db: AsyncSession, *, customer_id: uuid.UUID
    ) -> List[CustomerSolution]:
        """Get all active solutions for a customer"""
        result = await db.execute(
            select(CustomerSolution).filter(
                CustomerSolution.customer_id == customer_id,
                CustomerSolution.license_status == LicenseStatus.ACTIVE,
                (CustomerSolution.expiration_date >= date.today()) | (CustomerSolution.expiration_date.is_(None))
            )
        )
        return list(result.scalars().all())

    async def check_customer_has_access(
        self, db: AsyncSession, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> bool:
        """Check if customer has active access to a solution"""
        customer_solution = await self.get_by_customer_and_solution(
            db, customer_id=customer_id, solution_id=solution_id
        )
        if not customer_solution:
            return False
        
        if customer_solution.license_status != LicenseStatus.ACTIVE:
            return False
            
        if customer_solution.expiration_date and customer_solution.expiration_date < date.today():
            return False
            
        return True

    
    async def count_deployed_devices(
        self, db: AsyncSession, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> int:
        """Count number of customer's devices with this solution deployed"""
        
        # Join with device to make sure we're only counting customer's devices
        count_result = await db.execute(
            select(func.count())
            .select_from(DeviceSolution)
            .join(Device, DeviceSolution.device_id == Device.device_id)
            .filter(
                Device.customer_id == customer_id,
                DeviceSolution.solution_id == solution_id
            )
        )
        return count_result.scalar() or 0

    
    async def suspend(
        self, db: AsyncSession, *, id: uuid.UUID
    ) -> CustomerSolution:
        """Suspend a customer solution license"""
        customer_solution = await self.get_by_id(db, id=id)
        if customer_solution:
            customer_solution.license_status = LicenseStatus.SUSPENDED
            await db.commit()
            await db.refresh(customer_solution)
        return customer_solution

    
    async def activate(
        self, db: AsyncSession, *, id: uuid.UUID
    ) -> CustomerSolution:
        """Activate a customer solution license"""
        customer_solution = await self.get_by_id(db, id=id)
        if customer_solution:
            customer_solution.license_status = LicenseStatus.ACTIVE
            await db.commit()
            await db.refresh(customer_solution)
        return customer_solution


    async def get_enhanced_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """Get multiple customer solutions with enhanced solution details"""
        base_results = await self.get_multi(db, skip=skip, limit=limit)
        enhanced_results = []
        
        for cs in base_results:
            enhanced_cs = await self.get_by_customer_and_solution_enhanced(
                db, customer_id=cs.customer_id, solution_id=cs.solution_id
            )
            enhanced_results.append(enhanced_cs)
        
        return enhanced_results

    async def get_enhanced_by_customer(
        self, db: AsyncSession, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """Get customer solutions for a specific customer with enhanced solution details"""
        base_results = await self.get_by_customer(db, customer_id=customer_id, skip=skip, limit=limit)
        enhanced_results = []
        
        for cs in base_results:
            enhanced_cs = await self.get_by_customer_and_solution_enhanced(
                db, customer_id=cs.customer_id, solution_id=cs.solution_id
            )
            enhanced_results.append(enhanced_cs)
        
        return enhanced_results

    async def get_enhanced_by_solution(
        self, db: AsyncSession, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """Get customer solutions for a specific solution with enhanced solution details"""
        result = await db.execute(
            select(CustomerSolution)
            .filter(CustomerSolution.solution_id == solution_id)
            .offset(skip).limit(limit)
        )
        base_results = list(result.scalars().all())
        
        enhanced_results = []
        for cs in base_results:
            enhanced_cs = await self.get_by_customer_and_solution_enhanced(
                db, customer_id=cs.customer_id, solution_id=cs.solution_id
            )
            enhanced_results.append(enhanced_cs)
    
        return enhanced_results

    async def get_customer_solutions_with_details(
        self, 
        db: AsyncSession, 
        *, 
        customer_id: Optional[uuid.UUID] = None,
        solution_id: Optional[uuid.UUID] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get customer solutions with customer and solution details using efficient joins.
        Can filter by customer_id, solution_id, or both.
        Returns all data needed for CustomerSolutionAdminView.
        """
        # Start with a query that joins all three tables
        query = (
            select(
                CustomerSolution,
                Customer.name.label("customer_name"),
                Solution.name.label("solution_name")
            )
            .join(Customer, CustomerSolution.customer_id == Customer.customer_id)
            .join(Solution, CustomerSolution.solution_id == Solution.solution_id)
        )
        
        # Apply filters if provided
        if customer_id:
            query = query.filter(CustomerSolution.customer_id == customer_id)
        
        if solution_id:
            query = query.filter(CustomerSolution.solution_id == solution_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute the query
        results = (await db.execute(query)).all()
        
        # Process results into the expected format
        processed_results = []
        for result in results:
            cs, customer_name, solution_name = result

            # Count devices for this customer-solution pair
            devices_count = await self.count_deployed_devices(
                db, 
                customer_id=cs.customer_id, 
                solution_id=cs.solution_id
            )
            
            # Build the result dictionary
            cs_dict = {
                "id": cs.id,
                "customer_id": cs.customer_id,
                "solution_id": cs.solution_id,
                "license_status": cs.license_status,
                "expiration_date": cs.expiration_date,
                "configuration_template": cs.configuration_template,
                "created_at": cs.created_at,
                "updated_at": cs.updated_at,
                "customer_name": customer_name,
                "solution_name": solution_name,
                "devices_count": devices_count
            }
            
            processed_results.append(cs_dict)
        
        return processed_results


customer_solution = CRUDCustomerSolution(CustomerSolution)
