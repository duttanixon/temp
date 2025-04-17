# """
# Utility functions for tests.
# """
# import json
# import uuid
# from fastapi.testclient import TestClient
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta

# from app.core.config import settings
# from app.core.security import create_access_token

# def get_token_headers(token: str) -> dict:
#     """
#     Returns authorization headers with the token.
#     """
#     return {"Authorization": f"Bearer {token}"}

# def create_test_token(user_id: uuid.UUID, expires_minutes: int = 30) -> str:
#     """
#     Create a test JWT token for the given user_id.
#     """
#     return create_access_token(
#         subject=str(user_id),
#         expires_delta=timedelta(minutes=expires_minutes)
#     )

# def login_user(client: TestClient, email: str, password: str) -> dict:
#     """
#     Helper function to login a user and get a token.
#     Returns the response data which includes the token.
#     """
#     response = client.post(
#         f"{settings.API_V1_STR}/auth/login",
#         data={"username": email, "password": password}
#     )
    
#     if response.status_code != 200:
#         raise ValueError(f"Login failed with status {response.status_code}: {response.json()}")
    
#     return response.json()

# def create_test_customer(db: Session, name: str = None) -> dict:
#     """
#     Create a test customer and return its data.
#     """
#     from app.models.customer import Customer, CustomerStatus
    
#     # Generate a unique name if none provided
#     if name is None:
#         name = f"Test Customer {uuid.uuid4()}"
    
#     customer = Customer(
#         customer_id=uuid.uuid4(),
#         name=name,
#         contact_email=f"contact@{name.lower().replace(' ', '')}.com",
#         address=f"123 {name} Street",
#         status=CustomerStatus.ACTIVE
#     )
    
#     db.add(customer)
#     db.commit()
#     db.refresh(customer)
    
#     return {
#         "customer_id": customer.customer_id,
#         "name": customer.name,
#         "contact_email": customer.contact_email,
#         "address": customer.address,
#         "status": customer.status.value
#     }

# def create_test_user(db: Session, role: str, customer_id: uuid.UUID = None, email: str = None) -> dict:
#     """
#     Create a test user with the given role and customer_id.
#     Returns the user data including the password.
#     """
#     from app.models.user import User, UserRole, UserStatus
#     from app.core.security import get_password_hash
    
#     # Generate a unique email if none provided
#     if email is None:
#         email = f"{role.lower()}_{uuid.uuid4()}@example.com"
    
#     # Generate a password
#     password = f"password_{uuid.uuid4().hex[:8]}"
    
#     user = User(
#         user_id=uuid.uuid4(),
#         email=email,
#         password_hash=get_password_hash(password),
#         first_name=f"Test",
#         last_name=role.capitalize(),
#         role=getattr(UserRole, role.upper()),
#         customer_id=customer_id,
#         status=UserStatus.ACTIVE
#     )
    
#     db.add(user)
#     db.commit()
#     db.refresh(user)
    
#     return {
#         "user_id": user.user_id,
#         "email": user.email,
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "role": user.role.value,
#         "customer_id": user.customer_id,
#         "status": user.status.value,
#         "password": password  # Include the password for test login
#     }

# def get_audit_logs(db: Session, action_type: str = None, user_id: uuid.UUID = None, 
#                    resource_type: str = None, resource_id: str = None) -> list:
#     """
#     Query audit logs with optional filters.
#     Returns a list of audit log entries.
#     """
#     from app.models.audit_log import AuditLog
    
#     query = db.query(AuditLog)
    
#     if action_type:
#         query = query.filter(AuditLog.action_type == action_type)
    
#     if user_id:
#         query = query.filter(AuditLog.user_id == user_id)
    
#     if resource_type:
#         query = query.filter(AuditLog.resource_type == resource_type)
    
#     if resource_id:
#         query = query.filter(AuditLog.resource_id == resource_id)
    
#     # Order by timestamp, newest first
#     query = query.order_by(AuditLog.timestamp.desc())
    
#     return query.all()

# def assert_audit_log_exists(db: Session, action_type: str, user_id: uuid.UUID = None, 
#                             resource_type: str = None, resource_id: str = None) -> bool:
#     """
#     Assert that an audit log entry with the given parameters exists.
#     Returns True if found, raises AssertionError if not found.
#     """
#     logs = get_audit_logs(
#         db=db, 
#         action_type=action_type, 
#         user_id=user_id, 
#         resource_type=resource_type,
#         resource_id=resource_id
#     )
    
#     assert len(logs) > 0, f"No audit log found for action_type={action_type}"
#     return True