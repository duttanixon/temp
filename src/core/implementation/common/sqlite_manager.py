from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo


Base = declarative_base()

# Helper function to get current time in Tokyo timezone

def tokyo_time():
    return datetime.now(ZoneInfo("Asia/Tokyo"))


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self, base_dir: str):
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        # Create database file path
        db_path = os.path.join(self.data_dir, "edge_data.db")
        self.engine = create_engine(f"sqlite:///{db_path}")

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def cleanup(self):
        """Cleanup database connection"""
        self.engine.dispose()