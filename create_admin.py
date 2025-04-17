import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import uuid

# Add the project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.db.session import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

def create_admin_user(db: Session, email: str, password: str):
    """Create an admin user if it doesn't exist."""
    # Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"User with email {email} already exists.")
        return user
    
    # Create new admin user
    admin_user = User(
        user_id=uuid.uuid4(),
        email=email,
        password_hash=get_password_hash(password),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"Admin user created with email: {email}")
    return admin_user

if __name__ == "__main__":
    # Get admin credentials
    admin_email = input("Enter admin email: ")
    admin_password = input("Enter admin password: ")
    
    # Create database session
    db = SessionLocal()
    
    try:
        create_admin_user(db, admin_email, admin_password)
    finally:
        db.close()