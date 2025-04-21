import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from app.core.config import settings

# Define log levels dictionary for easier configuration
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

class CustomFormatter(logging.Formatter):
    """
    Custom formatter that adds additional information to log records
    """
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def formatTime(self, record, datefmt=None):
        # Use Japan timezone for consistent logs
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo("Asia/Tokyo"))
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S %z")

def setup_logger(
    logger_name: str = "app", 
    log_level: str = "info",
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_file_path: Optional[str] = None,
    max_log_file_size: int = 10 * 1024 * 1024,  # 10MB 
    log_file_backup_count: int = 5,
    rotate_logs_daily: bool = True
) -> logging.Logger:
    """
    Configure and return a logger instance
    
    Args:
        logger_name: Name of the logger
        log_level: Log level (debug, info, warning, error, critical)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        log_file_path: Path to log file
        max_log_file_size: Maximum size of log file before rotation
        log_file_backup_count: Number of backup log files to keep
        rotate_logs_daily: Whether to rotate logs daily
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)
    
    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    # Set log level
    logger.setLevel(LOG_LEVELS.get(log_level.lower(), logging.INFO))
    
    # Create formatter
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    formatter = CustomFormatter(log_format)
    # Add console handler if required
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if required
    if log_to_file:
        # Create log directory if it doesn't exist
        if not log_file_path:
            log_dir = settings.LOG_DIR if hasattr(settings, 'LOG_DIR') else './logs'
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = f"{log_dir}/{logger_name}.log"
        else:
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        if rotate_logs_daily:
            # Create a timed rotating file handler
            file_handler = TimedRotatingFileHandler(
                log_file_path, 
                when='midnight',
                interval=1,
                backupCount=log_file_backup_count
            )
        else:
            # Create a size-based rotating file handler
            file_handler = RotatingFileHandler(
                log_file_path, 
                maxBytes=max_log_file_size, 
                backupCount=log_file_backup_count
            )
            
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger

# Create main application logger
app_logger = setup_logger(
    logger_name="app",
    log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "info"
)

# Create API request logger
api_logger = setup_logger(
    logger_name="api",
    log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "info"
)

# Create DB operation logger
db_logger = setup_logger(
    logger_name="db",
    log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "info"
)

# Create auth operation logger
auth_logger = setup_logger(
    logger_name="auth",
    log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "info"
)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    If a logger with this name already exists, it will be returned
    Otherwise, a new logger will be created and configured
    
    Args:
        name: Name of the logger
    
    Returns:
        Logger instance
    """
    # Check if we already have a configured logger with this name
    existing_logger = logging.getLogger(name)
    
    # Only set up the logger if it hasn't been configured yet
    if not existing_logger.handlers:
        if name == "app":
            return app_logger
        elif name == "api":
            return api_logger
        elif name == "db":
            return db_logger
        elif name == "auth":
            return auth_logger
        else:
            # Configure a new logger with the given name
            return setup_logger(
                logger_name=name,
                log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "info"
            )
    
    return existing_logger