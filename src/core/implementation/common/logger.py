"""
Centralized logging module for the edge analytics application.
Provides structured logging with different severity levels, 
context information, and support for offline buffering and FluentBit integration.
"""

import logging
import json
import os
import time
import uuid
from datetime import datetime
import threading
import queue
from typing import Dict, Any, Optional, Union, List
import traceback
import socket
from zoneinfo import ZoneInfo
# Configure the basic logging system
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(funcName)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Default log directory
DEFAULT_LOG_DIR = "/var/log/edge-analytics"
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)


class StructuredLogger:
    """
    Structured logger that provides consistent log formatting
    with context information and error details.
    """

    # Singleton instance
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, log_dir: str = DEFAULT_LOG_DIR) -> "StructuredLogger":
        """Get singleton instance of the logger"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(log_dir)
        return cls._instance

    def __init__(self, log_dir: str = DEFAULT_LOG_DIR):
        """
        Initialize the structured logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("edge-analytics")
        self.logger.setLevel(logging.INFO)
        # self.logger.propagate = False

        # Create the primary file handler
        main_log_file = os.path.join(log_dir, "edge-analytics.log")
        main_handler = logging.FileHandler(main_log_file)
        main_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(funcName)s : %(message)s"
        )
        main_handler.setFormatter(formatter)
        self.logger.addHandler(main_handler)

        # Create error log file handler
        error_log_file = os.path.join(log_dir, "edge-analytics-error.log")
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

        # Create JSON structured log file
        self.structured_log_file = os.path.join(log_dir, "edge-analytics-structured.json")
        
        # Buffer for offline logging
        self.log_buffer = queue.Queue(maxsize=10000)
        self.buffer_processor = threading.Thread(target=self._process_buffer)
        self.buffer_processor.daemon = True
        self.buffer_processor.start()
        
        # Track connected state
        self.hostname = socket.gethostname()
        self.device_id = self._get_device_id()
        
        # Add console handler if in development
        if os.environ.get("EDGE_ENV") == "development":
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            console.setFormatter(formatter)
            self.logger.addHandler(console)

    def _get_device_id(self) -> str:
        """Get a unique device ID based on MAC address or configuration"""
        try:
            # Try to use the MAC address
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                        for elements in range(0, 2*6, 8)][::-1])
            return mac.replace(':', '-')
        except Exception as e:
            print(f"fallback- Error - {str(e)}")
            # Fallback to hostname
            return self.hostname

    def _process_buffer(self) -> None:
        """Background thread to process the log buffer"""
        while True:
            try:
                # Get up to 100 logs at a time
                logs = []
                for _ in range(100):
                    try:
                        log = self.log_buffer.get_nowait()
                        logs.append(log)
                    except queue.Empty:
                        break
                
                if logs:
                    # Write logs to structured log file
                    with open(self.structured_log_file, "a") as f:
                        for log in logs:
                            f.write(json.dumps(log) + "\n")
                
                # Prevent tight loop
                time.sleep(1)
            except Exception as e:
                print(f"Error processing log buffer: {e}")
                time.sleep(5)

    def _format_log(
        self, 
        level: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        component: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format a log message with context and exception information"""
        timestamp = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "hostname": self.hostname,
            "device_id": self.device_id,
        }
        
        if component:
            log_entry["component"] = component
            
        if context:
            log_entry["context"] = context
            
        if exception:
            log_entry["exception"] = {
                "type": exception.__class__.__name__,
                "message": str(exception),
                "traceback": traceback.format_exc(),
            }
            
        return log_entry

    def _log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        component: Optional[str] = None,
    ) -> None:
        """Log a message with context and exception information"""
        log_entry = self._format_log(level, message, context, exception, component)
        log_level_num = logging.getLevelName(level.upper())
        
        # Add to buffer for structured logging and possible FluentBit pickup
        if log_level_num >= self.logger.getEffectiveLevel():
            try:
                self.log_buffer.put_nowait(log_entry)
            except queue.Full:
                # If buffer is full, log a warning
                self.logger.warning("Log buffer full, dropping message")
            
        # Also log to standard logger
        log_method = getattr(self.logger, level.lower())
        if exception:
            log_method(f"{message} - {exception.__class__.__name__}: {str(exception)}", exc_info=exception, stacklevel=3)
        else:
            log_method(message, stacklevel=3)

    def debug(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None
    ) -> None:
        """Log a debug message"""
        self._log("DEBUG", message, context, component=component)

    def info(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None
    ) -> None:
        """Log an info message"""
        self._log("INFO", message, context, component=component)

    def warning(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        component: Optional[str] = None
    ) -> None:
        """Log a warning message"""
        self._log("WARNING", message, context, exception, component)

    def error(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        component: Optional[str] = None
    ) -> None:
        """Log an error message"""
        self._log("ERROR", message, context, exception, component)

    def critical(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        component: Optional[str] = None
    ) -> None:
        """Log a critical message"""
        self._log("CRITICAL", message, context, exception, component)


# Global instance for easy import
def get_logger() -> StructuredLogger:
    """Get the global logger instance"""
    return StructuredLogger.get_instance()