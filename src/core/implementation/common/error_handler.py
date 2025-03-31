"""
Error handler for the edge analytics application.
Provides centralized error handling, recovery strategies, and metrics tracking.
"""

import sys
import traceback
import threading
import time
from typing import Dict, Any, Callable, Optional, List, Tuple
from functools import wraps

from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import EdgeAnalyticsError, SystemErrors

logger = get_logger()


class ErrorMetrics:
    """Track error metrics for monitoring and alerting"""

    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, List[float]] = {}
        self.last_error: Optional[Tuple[str, str, float]] = None
        self._lock = threading.Lock()

    def record_error(self, error_type: str, error_message: str) -> None:
        """Record an error occurrence"""
        with self._lock:
            # Update error count
            if error_type not in self.error_counts:
                self.error_counts[error_type] = 0
                self.error_timestamps[error_type] = []
            
            self.error_counts[error_type] += 1
            current_time = time.time()
            self.error_timestamps[error_type].append(current_time)
            self.last_error = (error_type, error_message, current_time)
            
            # Clean up old timestamps (keep only last 24 hours)
            cutoff_time = current_time - 86400  # 24 hours in seconds
            self.error_timestamps[error_type] = [
                ts for ts in self.error_timestamps[error_type] if ts > cutoff_time
            ]

    def _get_error_rate(self, error_type: str, window_seconds: float = 3600) -> float:
        """Get the error rate for a specific error type in the given time window"""
        if error_type not in self.error_timestamps:
            return 0.0  
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        recent_errors = [
            ts for ts in self.error_timestamps[error_type] if ts > cutoff_time
        ]
        
        return len(recent_errors) / window_seconds * 3600 # per hour error rate

    def get_metrics(self) -> Dict[str, Any]:
        """Get error metrics for monitoring"""
        with self._lock:
            metrics = {
                "total_errors": sum(self.error_counts.values()),
                "error_types": list(self.error_counts.keys()),
                "error_counts": dict(self.error_counts),
                "error_rates": {
                    error_type: self._get_error_rate(error_type)
                    for error_type in self.error_counts
                }
            }
            
            if self.last_error:
                metrics["last_error"] = {
                    "type": self.last_error[0],
                    "message": self.last_error[1],
                    "timestamp": self.last_error[2]
                }
                
            return metrics


class ErrorHandler:
    """Centralized error handler"""

    # Singleton instance
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> 'ErrorHandler':
        """Get singleton instance of the error handler"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the error handler"""
        self.metrics = ErrorMetrics()
        self.recovery_strategies: Dict[str, Callable] = {}

        # Register default recovery strategies
        self.register_default_strategies()

    def register_default_strategies(self) -> None:
        """Register default recovery strategies for common errors"""
        # Connection errors - retry with backoff
        self.register_recovery_strategy(
            "ConnectionError", 
            lambda e, ctx: self._retry_with_backoff(e, ctx)
        )

        # # Pipeline errors - attempt restart
        # self.register_recovery_strategy(
        #     "PipelineError", 
        #     lambda e, ctx: self._restart_pipeline(e, ctx)
        # )

        # Resource exhaustion - free resources
        self.register_recovery_strategy(
            "ResourceExhaustedError", 
            lambda e, ctx: self._free_resources(e, ctx)
        )

    def register_recovery_strategy(
        self, 
        error_type: str, 
        strategy: Callable[[Exception, Dict[str, Any]],None]
    ) -> None:
        """Register a recovery strategy for an error type"""
        self.recovery_strategies[error_type] = strategy

    def handle_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None
    ) -> bool:
        """
        Handle an error with the appropriate recovery strategy.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            component: The component where the error occurred
            
        Returns:
            bool: True if the error was handled, False otherwise
        """
        context = context or {}
        error_type = error.__class__.__name__
        error_msg = str(error)
        # Log the error
        logger.error(
            f"Error in {component or 'unknown'}: {error_msg}",
            context=context,
            exception=error,
            component=component
        )

        # Record metrics
        self.metrics.record_error(error_type, error_msg)
        
        # Check if we have a recovery strategy
        if error_type in self.recovery_strategies:
            try:
                self.recovery_strategies[error_type](error, context)
                logger.info(
                    f"Applied recovery strategy for {error_type}",
                    context=context,
                    component=component
                )
                return True
            except Exception as recovery_error:
                logger.error(
                    f"Recovery strategy failed for {error_type}",
                    context=context,
                    exception=recovery_error,
                    component=component
                )
        
        # Check if it's a custom edge analytics error
        if isinstance(error, EdgeAnalyticsError) and error.recoverable:
            # Log that we're handling a recoverable error
            logger.info(
                f"Handling recoverable error: {error_type}",
                context=context,
                component=component
            )
            return True
            
        # We couldn't handle the error
        return False

    def _retry_with_backoff(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Retry operation with exponential backoff"""
        max_retries = context.get("max_retries", 5)
        current_retry = context.get("current_retry", 0)
        
        if current_retry < max_retries:
            # Calculate backoff time
            backoff_time = min(30, (2 ** current_retry))
            
            logger.info(
                f"Retry {current_retry+1}/{max_retries} after {backoff_time}s for {error.__class__.__name__}",
                context={"backoff_time": backoff_time, "retry": current_retry + 1}
            )
            
            # Sleep for backoff time
            time.sleep(backoff_time)
            
            # Update context for next retry
            context["current_retry"] = current_retry + 1
            
            # Execute retry function if provided
            retry_func = context.get("retry_function")
            if retry_func and callable(retry_func):
                retry_func()
        else:
            logger.error(
                f"Max retries ({max_retries}) exceeded for {error.__class__.__name__}",
                context=context,
                exception=error
            )
            raise SystemError("Max retries exceeded", details=context)

    def _restart_pipeline(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Attempt to restart the pipeline"""
        pipeline_manager = context.get("pipeline_manager")
        if not pipeline_manager:
            logger.error("Cannot restart pipeline: no pipeline manager in context")
            return
            
        try:
            # Get GST context from pipeline manager
            gst_context = pipeline_manager.context
            
            # Set pipeline to NULL state
            pipeline_manager.set_state(gst_context.gst.State.NULL)
            
            # Wait a moment
            time.sleep(1)
            
            # Recreate pipeline
            pipeline_string = context.get("pipeline_string")
            if pipeline_string:
                pipeline_manager.create_pipeline(pipeline_string)
                
                # Set up pipeline again
                pipeline_manager._setup_bus_handling()
                pipeline_manager._setup_callbacks()
                
                # Set pipeline to PLAYING state
                pipeline_manager.set_state(gst_context.gst.State.PLAYING)
                
                logger.info("Pipeline restarted successfully")
            else:
                logger.error("Cannot restart pipeline: no pipeline string in context")
        except Exception as e:
            logger.error(
                "Failed to restart pipeline", 
                exception=e,
                context=context
            )
            raise

    def _free_resources(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Free system resources"""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Forced garbage collection to free resources")


# Function decorators for easier error handling

def handle_errors(component: str = None):
    """
    Decorator to handle errors in a function.
    
    Args:
        component: The component name for logging
        
    Returns:
        The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = ErrorHandler.get_instance()
                if not error_handler.handle_error(e, context={"args": args, "kwargs": kwargs}, component=component):
                    # If the error wasn't handled, re-raise it
                    raise
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, retry_exceptions: List[Exception] = None):
    """
    Decorator to retry a function on specific exceptions.
    
    Args:
        max_retries: Maximum number of retries
        retry_exceptions: List of exceptions to retry on
        
    Returns:
        The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if we should retry this exception
                    should_retry = False
                    if retry_exceptions:
                        should_retry = any(isinstance(e, exc) for exc in retry_exceptions)
                    else:
                        # By default, retry all EdgeAnalyticsError with recoverable=True
                        should_retry = isinstance(e, EdgeAnalyticsError) and e.recoverable
                    
                    # If we shouldn't retry or have exceeded max retries, raise
                    if not should_retry or retries >= max_retries:
                        raise
                    
                    # Increment retry count
                    retries += 1
                    
                    # Calculate backoff time
                    backoff_time = min(30, (2 ** retries))
                    
                    # Log retry
                    logger.warning(
                        f"Retry {retries}/{max_retries} after {backoff_time}s for {e.__class__.__name__}",
                        context={"backoff_time": backoff_time, "retry": retries},
                        exception=e
                    )
                    
                    # Sleep for backoff time
                    time.sleep(backoff_time)
        return wrapper
    return decorator


# Global instance for easy import
def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return ErrorHandler.get_instance()