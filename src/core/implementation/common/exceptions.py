"""
Custom exception classes for the edge analytics application.
Provides a structured hierarchy of exceptions for better error handling and reporting.
"""

from typing import Dict, Any, Optional


class EdgeAnalyticsError(Exception):
    """Base exception for all edge analytics errors"""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.source = source
        self.recoverable = recoverable
        
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for structured logging"""
        return {
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "source": self.source,
            "recoverable": self.recoverable,
            "type": self.__class__.__name__
        }


# Configuration errors
class ConfigurationError(EdgeAnalyticsError):
    """Raised when there's an issue with configuration"""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when the configuration is invalid"""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing"""
    pass


# Input/Output errors
class IOError(EdgeAnalyticsError):
    """Base class for input/output errors"""
    pass


class InputSourceError(IOError):
    """Raised when there's an issue with the input source"""
    pass


class OutputHandlerError(IOError):
    """Raised when there's an issue with the output handler"""
    pass


class AppFileNotFoundError(IOError):
    """Raised when a file is not found"""
    pass


# Platform errors
class PlatformError(EdgeAnalyticsError):
    """Base class for platform-specific errors"""
    pass


class PipelineError(PlatformError):
    """Raised when there's an issue with the GStreamer pipeline"""
    pass


class HailoError(PlatformError):
    """Raised when there's an issue with the Hailo hardware"""
    pass


# Solution errors
class SolutionError(EdgeAnalyticsError):
    """Base class for solution-specific errors"""
    pass


class ProcessingError(SolutionError):
    """Raised when there's an issue with frame processing"""
    pass


class TrackingError(SolutionError):
    """Raised when there's an issue with object tracking"""
    pass

class DatabaseError(SolutionError):
    """Raosed when database initalization failed"""

# Cloud connectivity errors
class CloudError(EdgeAnalyticsError):
    """Base class for cloud connectivity errors"""
    pass


class ConnectionError(CloudError):
    """Raised when there's a connection issue"""
    pass


class AuthenticationError(CloudError):
    """Raised when there's an authentication issue"""
    pass


class SyncError(CloudError):
    """Raised when there's an issue syncing data to the cloud"""
    pass


# Hardware errors
class HardwareError(EdgeAnalyticsError):
    """Base class for hardware-related errors"""
    pass


class CameraError(HardwareError):
    """Raised when there's an issue with the camera"""
    pass


class AcceleratorError(HardwareError):
    """Raised when there's an issue with the accelerator hardware"""
    pass


# System errors
class SystemErrors(EdgeAnalyticsError):
    """Base class for system-level errors"""
    pass


class ResourceExhaustedError(SystemError):
    """Raised when system resources are exhausted"""
    pass


class MemoryError(SystemError):
    """Raised when there's a memory-related issue"""
    pass


class ThreadingError(SystemError):
    """Raised when there's an issue with threading"""
    pass