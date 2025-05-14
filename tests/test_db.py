"""
Database setup for testing.
This script can be run independently to create or rest the test database
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.core.security import get_password_hash
from app.db.session import Base
from app.models.user import User, UserRole, UserStatus
from app.models.customer import Customer, CustomerStatus
from app.models.audit_log import AuditLog

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Creat test engine and session
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_db():
    """Create tables and seed test data"""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        # Seed test data
        seed_test_data(db)
        
        # Commit the changes
        db.commit()
        print("Test database created and seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error setting up test database: {str(e)}")
    finally:
        db.close()

def drop_test_db():
    """Drop all tables in the test database"""
    Base.metadata.drop_all(bind=engine)
    print("Test database tables dropped.")

def seed_test_data(db):
    """Add test data to the database"""
    # Create test customers
    active_customer = Customer(
        customer_id=uuid.uuid4(),
        name="Test Customer",
        contact_email="contact@testcustomer.com",
        address="123 Test Street, Testville",
        status=CustomerStatus.ACTIVE
    )
    
    suspended_customer = Customer(
        customer_id=uuid.uuid4(),
        name="Suspended Customer",
        contact_email="contact@suspendedcustomer.com",
        address="456 Suspended Street, Testville",
        status=CustomerStatus.SUSPENDED
    )
    
    db.add(active_customer)
    db.add(suspended_customer)
    db.flush()  # Flush to get the IDs without committing
    
    # Create test users with different roles
    admin_user = User(
        user_id=uuid.uuid4(),
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE
    )
    
    engineer_user = User(
        user_id=uuid.uuid4(),
        email="engineer@example.com",
        password_hash=get_password_hash("engineerpassword"),
        first_name="Engineer",
        last_name="User",
        role=UserRole.ENGINEER,
        status=UserStatus.ACTIVE
    )
    
    customer_admin_user = User(
        user_id=uuid.uuid4(),
        email="customeradmin@example.com",
        password_hash=get_password_hash("customeradminpassword"),
        first_name="Customer",
        last_name="Admin",
        role=UserRole.CUSTOMER_ADMIN,
        customer_id=active_customer.customer_id,
        status=UserStatus.ACTIVE
    )
    
    suspended_user = User(
        user_id=uuid.uuid4(),
        email="suspended@example.com",
        password_hash=get_password_hash("suspendedpassword"),
        first_name="Suspended",
        last_name="User",
        role=UserRole.CUSTOMER_ADMIN,
        customer_id=active_customer.customer_id,
        status=UserStatus.SUSPENDED
    )
    
    db.add(admin_user)
    db.add(engineer_user)
    db.add(customer_admin_user)
    db.add(suspended_user)
    
    print("Added test users:")
    print(f"  Admin: {admin_user.email}")
    print(f"  Engineer: {engineer_user.email}")
    print(f"  Customer Admin: {customer_admin_user.email}")
    print(f"  Customer User: {customer_user.email}")
    print(f"  Suspended User: {suspended_user.email}")

if __name__ == "__main__":
    # If run directly, set up the test database
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_test_db()
    
    setup_test_db()