from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session
from app.crud.base import CRUDBase
from app.models import CustomerSolution, LicenseStatus, DeviceSolution, Device, Solution, Customer
from app.schemas.customer_solution import CustomerSolutionCreate, CustomerSolutionUpdate
import uuid
from datetime import date

class CRUDCustomerSolution(CRUDBase[CustomerSolution, CustomerSolutionCreate, CustomerSolutionUpdate]):
    def get_by_id(self, db: Session, *, id: uuid.UUID) -> Optional[CustomerSolution]:
        return db.query(CustomerSolution).filter(CustomerSolution.id == id).first()

    def get_by_customer_and_solution(
        self, db: Session, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> Optional[CustomerSolution]:
        return db.query(CustomerSolution).filter(
            CustomerSolution.customer_id == customer_id,
            CustomerSolution.solution_id == solution_id
        ).first()

    def get_by_customer_and_solution_enhanced(
        self, db: Session, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> Optional[CustomerSolution]:
        # First get the customer solution record
        cs = db.query(CustomerSolution).filter(
            CustomerSolution.customer_id == customer_id,
            CustomerSolution.solution_id == solution_id
        ).first()

        # If no customer solution record is found, return None
        if not cs:
            return None

        # Get the solution details
        sol = db.query(Solution).filter(Solution.solution_id == solution_id).first()
        
        # Combine data
        result = cs.__dict__.copy()
        if sol:
            result["solution_name"] = sol.name
            result["solution_version"] = sol.version
        devices_count = db.query(DeviceSolution).join(
            Device, DeviceSolution.device_id == Device.device_id
        ).filter(
            Device.customer_id == customer_id,
            DeviceSolution.solution_id == solution_id
        ).count()
        
        result["devices_count"] = devices_count
        return result
    
    def get_by_customer(
        self, db: Session, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[CustomerSolution]:
        return db.query(CustomerSolution).filter(
            CustomerSolution.customer_id == customer_id
        ).offset(skip).limit(limit).all()

    def get_active_by_customer(
        self, db: Session, *, customer_id: uuid.UUID
    ) -> List[CustomerSolution]:
        """Get all active solutions for a customer"""
        return db.query(CustomerSolution).filter(
            CustomerSolution.customer_id == customer_id,
            CustomerSolution.license_status == LicenseStatus.ACTIVE,
            (CustomerSolution.expiration_date >= date.today()) | (CustomerSolution.expiration_date.is_(None))
        ).all()

    def check_customer_has_access(
        self, db: Session, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> bool:
        """Check if customer has active access to a solution"""
        customer_solution = self.get_by_customer_and_solution(
            db, customer_id=customer_id, solution_id=solution_id
        )
        if not customer_solution:
            return False
        
        if customer_solution.license_status != LicenseStatus.ACTIVE:
            return False
            
        if customer_solution.expiration_date and customer_solution.expiration_date < date.today():
            return False
            
        return True

    
    def count_deployed_devices(
        self, db: Session, *, customer_id: uuid.UUID, solution_id: uuid.UUID
    ) -> int:
        """Count number of customer's devices with this solution deployed"""
        
        # Join with device to make sure we're only counting customer's devices
        return db.query(DeviceSolution).join(
            Device, DeviceSolution.device_id == Device.device_id
        ).filter(
            Device.customer_id == customer_id,
            DeviceSolution.solution_id == solution_id
        ).count()

    
    def suspend(
        self, db: Session, *, id: uuid.UUID
    ) -> CustomerSolution:
        """Suspend a customer solution license"""
        customer_solution = self.get_by_id(db, id=id)
        customer_solution.license_status = LicenseStatus.SUSPENDED
        db.add(customer_solution)
        db.commit()
        db.refresh(customer_solution)
        return customer_solution

    
    def activate(
        self, db: Session, *, id: uuid.UUID
    ) -> CustomerSolution:
        """Activate a customer solution license"""
        customer_solution = self.get_by_id(db, id=id)
        customer_solution.license_status = LicenseStatus.ACTIVE
        db.add(customer_solution)
        db.commit()
        db.refresh(customer_solution)
        return customer_solution


    def get_enhanced_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """Get multiple customer solutions with enhanced solution details"""
        base_results = self.get_multi(db, skip=skip, limit=limit)
        enhanced_results = []
        
        for cs in base_results:
            enhanced_cs = self.get_by_customer_and_solution_enhanced(
                db, customer_id=cs.customer_id, solution_id=cs.solution_id
            )
            enhanced_results.append(enhanced_cs)
        
        return enhanced_results

    def get_enhanced_by_customer(
        self, db: Session, *, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """Get customer solutions for a specific customer with enhanced solution details"""
        base_results = self.get_by_customer(db, customer_id=customer_id, skip=skip, limit=limit)
        enhanced_results = []
        
        for cs in base_results:
            enhanced_cs = self.get_by_customer_and_solution_enhanced(
                db, customer_id=cs.customer_id, solution_id=cs.solution_id
            )
            enhanced_results.append(enhanced_cs)
        
        return enhanced_results

    def get_enhanced_by_solution(
        self, db: Session, *, solution_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """Get customer solutions for a specific solution with enhanced solution details"""
        base_results = db.query(CustomerSolution).filter(
            CustomerSolution.solution_id == solution_id
        ).offset(skip).limit(limit).all()
        
        enhanced_results = []
        for cs in base_results:
            enhanced_cs = self.get_by_customer_and_solution_enhanced(
                db, customer_id=cs.customer_id, solution_id=cs.solution_id
            )
            enhanced_results.append(enhanced_cs)
    
        return enhanced_results

    def get_customer_solutions_with_details(
        self, 
        db: Session, 
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
            db.query(
                CustomerSolution,
                Customer.name.label("customer_name"),
                Solution.name.label("solution_name"),
                Solution.version.label("solution_version")
            )
            .join(Customer, CustomerSolution.customer_id == Customer.customer_id)
            .join(Solution, CustomerSolution.solution_id == Solution.solution_id)
        )
        
        # Apply filters if provided
        if customer_id:
            query = query.filter(CustomerSolution.customer_id == customer_id)
        
        if solution_id:
            query = query.filter(CustomerSolution.solution_id == solution_id)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute the query
        results = query.all()
        
        # Process results into the expected format
        processed_results = []
        for result in results:
            cs, customer_name, solution_name, solution_version = result
            
            # Count devices for this customer-solution pair
            devices_count = self.count_deployed_devices(
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
                "max_devices": cs.max_devices,
                "expiration_date": cs.expiration_date,
                "configuration_template": cs.configuration_template,
                "created_at": cs.created_at,
                "updated_at": cs.updated_at,
                "customer_name": customer_name,
                "solution_name": solution_name,
                "solution_version": solution_version,
                "devices_count": devices_count
            }
            
            processed_results.append(cs_dict)
        
        return processed_results


customer_solution = CRUDCustomerSolution(CustomerSolution)