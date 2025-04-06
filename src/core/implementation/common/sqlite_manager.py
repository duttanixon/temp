from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Generator

from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import DatabaseError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()


Base = declarative_base()

# Helper function to get current time in Tokyo timezone

def tokyo_time():
    return datetime.now(ZoneInfo("Asia/Tokyo"))


class DatabaseManager:
    """Manages database connections and sessions"""

    def __init__(self, base_dir: str):
        """
        Initialize the database manager.
        
        Args:
            base_dir: Base directory for database files
            
        Raises:
            DatabaseError: If database initialization fails
        """
        try:
            # Create data directory if it doesn't exist
            self.data_dir = os.path.join(base_dir, "data")
            os.makedirs(self.data_dir, exist_ok=True)

            # Create database file path
            db_path = os.path.join(self.data_dir, "edge_data.db")
            logger.info(
                "Initializing database",
                context={"db_path": db_path},
                component="DatabaseManager"
            )

           # Create SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{db_path}")

            # Create tables
            Base.metadata.create_all(self.engine)

            # Create session factory
            self.Session = sessionmaker(bind=self.engine)

            logger.info("Database initialized successfully", component="DatabaseManager")


        except Exception as e:
            error_msg = "Failed to initialize database"
            logger.error(
                error_msg,
                exception=e,
                context={"base_dir": base_dir},
                component="DatabaseManager"
            )
            raise DatabaseError(
                error_msg,
                code="DB_INIT_FAILED",
                details={"base_dir": base_dir, "error": str(e)},
                source="DatabaseManager"
            ) from e

    @contextmanager
    @handle_errors(component="DatabaseManager")
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Yields:
            SQLAlchemy session
            
        Raises:
            DatabaseError: If session operations fail
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(
                "Error in database session, rolling back",
                exception=e,
                component="DatabaseManager"
            )
            session.rollback()
            raise DatabaseError(
                "Database operation failed",
                code="DB_OPERATION_FAILED",
                details={"error": str(e)},
                source="DatabaseManager"
            ) from e
        finally:
            session.close()

    def cleanup(self):
        """
        Clean up database resources.
        
        Raises:
            DatabaseError: If cleanup fails
        """
        try:
            if hasattr(self, 'engine'):
                logger.info("Cleaning up database resources", component="DatabaseManager")
                self.engine.dispose()
                logger.info("Database resources cleaned up", component="DatabaseManager")
        except Exception as e:
            error_msg = "Error cleaning up database resources"
            logger.error(
                error_msg,
                exception=e,
                component="DatabaseManager"
            )
            raise DatabaseError(
                error_msg,
                code="DB_CLEANUP_FAILED",
                details={"error": str(e)},
                source="DatabaseManager"
            ) from e