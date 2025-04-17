"""
This file contains shared fixtures for pytest to use accross all test files.
It handles database setup, test clients and authentication helpers.
"""
import os
import pytest
import uuid
from typing import Dict, Generator, List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app
from app.models.user import User, UserRole, UserStatus
from app.models.customer import Customer, CustomerStatus

# Test database URL - use SQLite for tests 
TEST_DATABASE_URL = f"sqlite:///./test.db"

# Create test engine and session
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db() -> Generator:
    """
    Create a fresh database for each test and yield a session.
    After the test completes, rollback any changes and drop all tables.
    """

    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Create a db session
    session = TestingSessionLocal()

    # Create a db session
    session = TestingSessionLocal()

    # Create test data
    seed_test_data(session)

    yield session

    # Teardown
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client() -> Generator:
    """
    Create a FastAPI TestClient for making test requests.
    """
    with TestClient(app) as c:
        yield c

# Helper fixtures for creating test tokens and users

@pytest.fixture
def admin_user(db: Session) -> User:
    """Get the admin user created by the seed function"""
    return db.query(User).filter(User.role == UserRole.ADMIN).first()

@pytest.fixture
def engineer_user(db: Session) -> User:
    """Get the engineer user created by the seed function"""
    return db.query(User).filter(User.role == UserRole.ENGINEER).first()

@pytest.fixture
def customer_admin_user(db: Session) -> User:
    """Get the customer admin user created by the seed function"""
    return db.query(User).filter(User.role == UserRole.CUSTOMER_ADMIN).first()

@pytest.fixture
def customer_user(db: Session) -> User:
    """Get the customer user created by the seed function"""
    return db.query(User).filter(User.role == UserRole.CUSTOMER_USER).first()

@pytest.fixture
def suspended_user(db: Session) -> User:
    """Get the suspended user created by the seed function"""
    return db.query(User).filter(User.status == UserStatus.SUSPENDED).first()

@pytest.fixture
def customer(db: Session) -> Customer:
    """Get the customer created by the seed function"""
    return db.query(Customer).filter(Customer.status == CustomerStatus.ACTIVE).first()

@pytest.fixture
def suspended_customer(db: Session) -> Customer:
    """Get the suspended customer created by the seed function"""
    return db.query(Customer).filter(Customer.status == CustomerStatus.SUSPENDED).first()


# Token fixtures

@pytest.fixture
def admin_token(admin_user: User) -> str:
    """Generate an admin token for tests"""
    return create_access_token(
        subject=str(admin_user.user_id),
        expires_delta=timedelta(minutes=30),
        role=UserRole.ADMIN.value
    )

@pytest.fixture
def engineer_token(engineer_user: User) -> str:
    """Generate an engineer token for tests"""
    return create_access_token(
        subject=str(engineer_user.user_id),
        expires_delta=timedelta(minutes=30)
    )

@pytest.fixture
def customer_admin_token(customer_admin_user: User) -> str:
    """Generate a customer admin token for tests"""
    return create_access_token(
        subject=str(customer_admin_user.user_id),
        expires_delta=timedelta(minutes=30)
    )

@pytest.fixture
def customer_user_token(customer_user: User) -> str:
    """Generate a customer user token for tests"""
    return create_access_token(
        subject=str(customer_user.user_id),
        expires_delta=timedelta(minutes=30)
    )

@pytest.fixture
def suspended_user_token(suspended_user: User) -> str:
    """Generate a suspended user token for tests"""
    return create_access_token(
        subject=str(suspended_user.user_id),
        expires_delta=timedelta(minutes=30)
    )

@pytest.fixture
def expired_token(admin_user: User) -> str:
    """Generate an expired token for tests"""
    return create_access_token(
        subject=str(admin_user.user_id),
        expires_delta=timedelta(minutes=-30)  # Negative minutes = expired
    )


def seed_test_data(db: Session) -> None:
    """
    Populate the test database with sample data for testing
    """
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
    db.commit()
    
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
    
    customer_user = User(
        user_id=uuid.uuid4(),
        email="customeruser@example.com",
        password_hash=get_password_hash("customeruserpassword"),
        first_name="Customer",
        last_name="User",
        role=UserRole.CUSTOMER_USER,
        customer_id=active_customer.customer_id,
        status=UserStatus.ACTIVE
    )
    
    suspended_user = User(
        user_id=uuid.uuid4(),
        email="suspended@example.com",
        password_hash=get_password_hash("suspendedpassword"),
        first_name="Suspended",
        last_name="User",
        role=UserRole.CUSTOMER_USER,
        customer_id=active_customer.customer_id,
        status=UserStatus.SUSPENDED
    )
    
    db.add(admin_user)
    db.add(engineer_user)
    db.add(customer_admin_user)
    db.add(customer_user)
    db.add(suspended_user)
    db.commit()