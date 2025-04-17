# """
# Test cases for audit logging functionality.
# """
# import pytest
# import uuid
# from sqlalchemy.orm import Session

# from app.utils.audit import log_action
# from app.models.audit_log import AuditLog

# def test_log_action_basic(db: Session):
#     """Test basic audit logging functionality"""
#     # Create test data
#     user_id = uuid.uuid4()
#     action_type = "TEST_ACTION"
#     resource_type = "TEST_RESOURCE"
#     resource_id = "test-123"
    
#     # Log the action
#     log_entry = log_action(
#         db=db,
#         user_id=user_id,
#         action_type=action_type,
#         resource_type=resource_type,
#         resource_id=resource_id
#     )
    
#     # Verify log entry was created
#     assert log_entry is not None
#     assert log_entry.user_id == user_id
#     assert log_entry.action_type == action_type
#     assert log_entry.resource_type == resource_type
#     assert log_entry.resource_id == resource_id
    
#     # Verify log entry exists in database
#     db_log = db.query(AuditLog).filter(AuditLog.log_id == log_entry.log_id).first()
#     assert db_log is not None
#     assert db_log.resource_id == resource_id

# def test_log_action_with_details(db: Session):
#     """Test audit logging with details JSON"""
#     # Create test data
#     user_id = uuid.uuid4()
#     action_type = "TEST_ACTION_DETAILS"
#     resource_type = "TEST_RESOURCE"
#     resource_id = "test-456"
#     details = {
#         "key1": "value1",
#         "key2": 123,
#         "nested": {
#             "subkey": "subvalue"
#         }
#     }
    
#     # Log the action
#     log_entry = log_action(
#         db=db,
#         user_id=user_id,
#         action_type=action_type,
#         resource_type=resource_type,
#         resource_id=resource_id,
#         details=details
#     )
    
#     # Verify log entry was created with details
#     assert log_entry is not None
#     assert log_entry.details is not None
#     assert log_entry.details["key1"] == "value1"
#     assert log_entry.details["key2"] == 123
#     assert log_entry.details["nested"]["subkey"] == "subvalue"

# def test_log_action_no_user(db: Session):
#     """Test audit logging without a user ID (system action)"""
#     # Log the action without user_id
#     log_entry = log_action(
#         db=db,
#         user_id=None,
#         action_type="SYSTEM_ACTION",
#         resource_type="SYSTEM",
#         resource_id="system-123"
#     )
    
#     # Verify log entry was created
#     assert log_entry is not None
#     assert log_entry.user_id is None
#     assert log_entry.action_type == "SYSTEM_ACTION"

# def test_log_action_with_ip_useragent(db: Session):
#     """Test audit logging with IP address and user agent"""
#     # Create test data
#     user_id = uuid.uuid4()
#     ip_address = "192.168.1.1"
#     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
#     # Log the action
#     log_entry = log_action(
#         db=db,
#         user_id=user_id,
#         action_type="LOGIN",
#         resource_type="USER",
#         resource_id="user-123",
#         ip_address=ip_address,
#         user_agent=user_agent
#     )
    
#     # Verify log entry was created with IP and user agent
#     assert log_entry is not None
#     assert log_entry.ip_address == ip_address
#     assert log_entry.user_agent == user_agent