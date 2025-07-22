"""
This file contains shared fixtures for pytest to use accross all test files.
It handles database setup, test clients and authentication helpers.
"""
import os
import pytest
import uuid
from typing import Dict, Generator, List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, JSON
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timedelta
# Add these imports for JSONB support in SQLite
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app
from app.models import (
    User, UserRole, UserStatus, Customer, CustomerStatus, Device, DeviceStatus, 
    DeviceType, Solution, CustomerSolution, DeviceSolution, DeviceSolutionStatus, 
    LicenseStatus, SolutionStatus, CityEyeHumanTable, CityEyeTrafficTable, DeviceCommand
)

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

# Add this to make JSONB work with SQLite
@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(element, compiler, **kw):
    # Use JSON type for SQLite instead of JSONB
    return compiler.visit_JSON(element, **kw)

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
def customer_admin_user2(db: Session) -> User:
    """Get the customer admin user created by the seed function"""
    return db.query(User).filter(User.role == UserRole.CUSTOMER_ADMIN, User.email == "customeradmin@example2.com").first()


@pytest.fixture
def suspended_user(db: Session) -> User:
    """Get the suspended user created by the seed function"""
    return db.query(User).filter(User.status == UserStatus.SUSPENDED).first()

@pytest.fixture
def customer(db: Session) -> Customer:
    """Get the customer created by the seed function"""
    return db.query(Customer).filter(Customer.status == CustomerStatus.ACTIVE).first()

@pytest.fixture
def solution(db: Session) -> Solution:
    """Get a solution created by the seed function"""
    return db.query(Solution).filter(Solution.status == SolutionStatus.ACTIVE).first()

@pytest.fixture
def beta_solution(db: Session) -> Solution:
    """Get a beta solution created by the seed function"""
    return db.query(Solution).filter(Solution.status == SolutionStatus.BETA).first()

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
def customer_admin_token2(customer_admin_user2: User) -> str:
    """Generate a customer admin token for tests"""
    return create_access_token(
        subject=str(customer_admin_user2.user_id),
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

@pytest.fixture
def device(db: Session, customer: Customer) -> Device:
    """Get a basic test device created by the seed function"""
    return db.query(Device).filter(Device.device_type == DeviceType.NVIDIA_JETSON).first()

@pytest.fixture
def raspberry_device(db: Session, customer: Customer) -> Device:
    """Get a Raspberry Pi test device created by the seed function"""
    return db.query(Device).filter(Device.device_type == DeviceType.RASPBERRY_PI).first()

@pytest.fixture
def provisioned_device(db: Session, customer: Customer) -> Device:
    """Get a provisioned device created by the seed function"""
    return db.query(Device).filter(Device.status == DeviceStatus.PROVISIONED).first()

@pytest.fixture
def active_device(db: Session, customer: Customer) -> Device:
    """Get an active device created by the seed function"""
    return db.query(Device).filter(Device.status == DeviceStatus.ACTIVE).first()


@pytest.fixture
def test_customer_solution(db: Session, customer: Customer) -> CustomerSolution:
    """Get a customer solution created by the seed function"""
    return db.query(CustomerSolution).filter(
        CustomerSolution.customer_id == customer.customer_id
    ).first()

@pytest.fixture
def suspended_customer_solution(db: Session, suspended_customer: Customer, admin_token: str, 
                               client: TestClient) -> CustomerSolution:
    """Create a customer solution for the suspended customer"""
    # First check if one already exists
    existing = db.query(CustomerSolution).filter(
        CustomerSolution.customer_id == suspended_customer.customer_id
    ).first()
    
    if existing:
        return existing
    
    # Create a new one if it doesn't exist
    solution_obj = db.query(Solution).first()
    
    new_cs = CustomerSolution(
        id=uuid.uuid4(),
        customer_id=suspended_customer.customer_id,
        solution_id=solution_obj.solution_id,
        license_status=LicenseStatus.ACTIVE,
        max_devices=5
    )
    db.add(new_cs)
    db.commit()
    db.refresh(new_cs)
    
    return new_cs

# City Eye specific fixtures
@pytest.fixture
def city_eye_solution(db: Session) -> Solution:
    """Get or create City Eye solution for testing"""
    city_eye = db.query(Solution).filter(Solution.name == "City Eye").first()
    if not city_eye:
        city_eye = Solution(
            solution_id=uuid.uuid4(),
            name="City Eye",
            description="City Eye human flow analytics solution",
            version="1.0.0",
            compatibility=["NVIDIA_JETSON", "RASPBERRY_PI"],
            status=SolutionStatus.ACTIVE
        )
        db.add(city_eye)
        db.commit()
        db.refresh(city_eye)
    return city_eye

@pytest.fixture
def city_eye_customer_solution(db: Session, customer: Customer, city_eye_solution: Solution) -> CustomerSolution:
    """Create customer solution access for City Eye"""
    existing = db.query(CustomerSolution).filter(
        CustomerSolution.customer_id == customer.customer_id,
        CustomerSolution.solution_id == city_eye_solution.solution_id
    ).first()
    
    if existing:
        return existing
    
    customer_solution = CustomerSolution(
        id=uuid.uuid4(),
        customer_id=customer.customer_id,
        solution_id=city_eye_solution.solution_id,
        license_status=LicenseStatus.ACTIVE,
        max_devices=10
    )
    db.add(customer_solution)
    db.commit()
    db.refresh(customer_solution)
    return customer_solution


@pytest.fixture
def city_eye_device_solution(db: Session, device: Device, city_eye_solution: Solution) -> DeviceSolution:
    """Create device solution deployment for City Eye"""
    existing = db.query(DeviceSolution).filter(
        DeviceSolution.device_id == device.device_id,
        DeviceSolution.solution_id == city_eye_solution.solution_id
    ).first()
    
    if existing:
        return existing
    
    device_solution = DeviceSolution(
        id=uuid.uuid4(),
        device_id=device.device_id,
        solution_id=city_eye_solution.solution_id,
        status=DeviceSolutionStatus.ACTIVE,
        version_deployed="1.0.0",
        configuration={"param1": "value1"}
    )
    db.add(device_solution)
    db.commit()
    db.refresh(device_solution)
    return device_solution

@pytest.fixture
def city_eye_analytics_data(db: Session, device: Device, city_eye_solution: Solution, city_eye_device_solution: DeviceSolution):
    """Create test analytics data for City Eye"""
    base_time = datetime.now()
    
    # Create sample human flow data
    test_data = [
        CityEyeHumanTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=base_time,
            polygon_id_in="1",
            polygon_id_out="1",
            male_less_than_18=5,
            female_less_than_18=3,
            male_18_to_29=10,
            female_18_to_29=8,
            male_30_to_49=15,
            female_30_to_49=12,
            male_50_to_64=7,
            female_50_to_64=6,
            male_65_plus=2,
            female_65_plus=4
        ),
        CityEyeHumanTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=base_time + timedelta(hours=1),
            polygon_id_in="2",
            polygon_id_out="2",
            male_less_than_18=3,
            female_less_than_18=4,
            male_18_to_29=12,
            female_18_to_29=9,
            male_30_to_49=18,
            female_30_to_49=14,
            male_50_to_64=8,
            female_50_to_64=7,
            male_65_plus=3,
            female_65_plus=5
        )
    ]
    
    for data in test_data:
        db.add(data)
    db.commit()
    
    return test_data

@pytest.fixture
def city_eye_traffic_data(db: Session, device: Device, city_eye_solution: Solution, city_eye_device_solution: DeviceSolution):
    """Create test traffic analytics data for City Eye"""
    base_time = datetime.now()
    
    # Create sample traffic flow data
    test_data = [
        CityEyeTrafficTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=base_time,
            polygon_id_in="1",
            polygon_id_out="1",
            large=5,
            normal=15,
            bicycle=8,
            motorcycle=3
        ),
        CityEyeTrafficTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=base_time + timedelta(hours=1),
            polygon_id_in="2",
            polygon_id_out="2",
            large=7,
            normal=20,
            bicycle=12,
            motorcycle=5
        )
    ]
    
    for data in test_data:
        db.add(data)
    db.commit()
    
    return test_data

@pytest.fixture(scope="function")
def city_eye_human_direction_analytics_data(db: Session, device: Device, city_eye_solution: Solution, city_eye_device_solution: DeviceSolution):
    """Fixture to create human direction analytics data for testing."""
    data = [
        CityEyeHumanTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=datetime.now() - timedelta(hours=1),
            polygon_id_in="0",
            polygon_id_out="1",
            male_18_to_29=2,
            female_30_to_39=1,
        ),
        CityEyeHumanTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=datetime.now(),
            polygon_id_in="1",
            polygon_id_out="0",
            female_18_to_29=3,
        ),
    ]
    db.add_all(data)
    db.commit()
    return data


@pytest.fixture(scope="function")
def city_eye_traffic_direction_analytics_data(db: Session, device: Device, city_eye_solution: Solution, city_eye_device_solution: DeviceSolution):
    """Fixture to create traffic direction analytics data for testing."""
    data = [
        CityEyeTrafficTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=datetime.now() - timedelta(minutes=30),
            polygon_id_in="0",
            polygon_id_out="1",
            normal=5,
            large=1,
            bicycle=2,
            motorcycle=3,
        ),
        CityEyeTrafficTable(
            device_id=device.device_id,
            solution_id=city_eye_solution.solution_id,
            device_solution_id=city_eye_device_solution.id,
            timestamp=datetime.now(),
            polygon_id_in="1",
            polygon_id_out="0",
            normal=10,
        ),
    ]
    db.add_all(data)
    db.commit()
    return data

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

    customer_admin_user2 = User(
        user_id=uuid.uuid4(),
        email="customeradmin@example2.com",
        password_hash=get_password_hash("customeradminpassword"),
        first_name="Customer2",
        last_name="Admin2",
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
    # Create test devices
    basic_device = Device(
        device_id=uuid.uuid4(),
        name="Test Device",
        description="A test device for testing",
        mac_address="00:11:22:33:44:55",
        serial_number="SN123456789",
        device_type=DeviceType.NVIDIA_JETSON,
        firmware_version="1.0.0",
        location="Test Location",
        customer_id=active_customer.customer_id,
        ip_address="192.168.1.100",
        status=DeviceStatus.PROVISIONED,
        is_online=False
    )
    
    raspberry_device = Device(
        device_id=uuid.uuid4(),
        name="Raspberry Pi Device",
        description="A Raspberry Pi test device",
        mac_address="AA:BB:CC:DD:EE:FF",
        serial_number="SNRPI123456",
        device_type=DeviceType.RASPBERRY_PI,
        firmware_version="2.0.0",
        location="Pi Location",
        customer_id=active_customer.customer_id,
        ip_address="192.168.1.200",
        status=DeviceStatus.DECOMMISSIONED,
        is_online=False
    )
    
    active_device = Device(
        device_id=uuid.uuid4(),
        name="Active Device",
        description="An active test device",
        mac_address="11:22:33:44:55:66",
        serial_number="SNACTIVE123",
        device_type=DeviceType.NVIDIA_JETSON,
        firmware_version="1.5.0",
        location="Active Location",
        customer_id=active_customer.customer_id,
        ip_address="192.168.1.150",
        status=DeviceStatus.ACTIVE,
        is_online=True,
        thing_name="active-device-thing",
        thing_arn="arn:aws:iot:region:account:thing/active-device-thing",
        certificate_id="cert123",
        certificate_arn="arn:aws:iot:region:account:cert/cert123"
    )
    
    suspended_device = Device(
        device_id=uuid.uuid4(),
        name="Suspended Customer Device",
        description="A device for the suspended customer",
        mac_address="66:77:88:99:AA:BB",
        serial_number="SNSUSPENDED",
        device_type=DeviceType.NVIDIA_JETSON,
        firmware_version="1.0.0",
        location="Suspended Location",
        customer_id=suspended_customer.customer_id,
        status=DeviceStatus.DECOMMISSIONED,
        is_online=False
    )


    # Create test solutions
    test_solution = Solution(
        solution_id=uuid.uuid4(),
        name="Test Solution",
        description="A test solution for device management",
        version="1.0.0",
        compatibility=["NVIDIA_JETSON", "RASPBERRY_PI"],
        status=SolutionStatus.ACTIVE
    )
    
    beta_solution = Solution(
        solution_id=uuid.uuid4(),
        name="Beta Solution",
        description="A beta solution for testing",
        version="0.5.0",
        compatibility=["NVIDIA_JETSON"],
        status=SolutionStatus.BETA
    )

    # Create customer-solution relationships
    test_customer_solution = CustomerSolution(
        id=uuid.uuid4(),
        customer_id=active_customer.customer_id,
        solution_id=test_solution.solution_id,
        license_status=LicenseStatus.ACTIVE,
        max_devices=10
    )
    
    # Create device-solution deployment
    test_device_solution = DeviceSolution(
        id=uuid.uuid4(),
        device_id=active_device.device_id,
        solution_id=test_solution.solution_id,
        status=DeviceSolutionStatus.ACTIVE,
        version_deployed=test_solution.version,
        configuration={"param1": "value1", "param2": "value2"}
    )
    
    db.add(admin_user)
    db.add(engineer_user)
    db.add(customer_admin_user)
    db.add(customer_admin_user2)
    db.add(suspended_user)
    db.add(basic_device)
    db.add(raspberry_device)
    db.add(active_device)
    db.add(suspended_device)
    db.add(test_solution)
    db.add(beta_solution)
    db.add(test_customer_solution)
    db.add(test_device_solution)
    db.commit()