
"""
Frame processor module for CityEye solution.
Handles frame processing, queuing, and worker thread management.
"""
from typing import Any, Dict, Optional
import threading
import time
from queue import Queue, Empty, Full
from datetime import datetime
from zoneinfo import ZoneInfo
import threading

from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ProcessingError

logger = get_logger()


class FrameProcessor:
    """Handles frame processing logic with queue management and worker threads."""
    
    def __init__(self, max_queue_size: int = 100, command_queue_size: int = 50):
        """
        Initialize the frame processor.
        
        Args:
            max_queue_size: Maximum size of the frame queue
            command_queue_size: Maximum size of the command queue
        """
        self.component_name = self.__class__.__name__
        self.frame_queue = Queue(maxsize=max_queue_size)
        self.command_queue = Queue(maxsize=command_queue_size)

        # for image capture requests
        self._current_capture_request: Optional[Dict[str, Any]] = None
        self._capture_requested = threading.Event()

        self.running = False
        self.worker_thread = None
        # Frame processing callbacks
        self._frame_callback = None
        self._command_callback = None
        self._capture_callback = None
        
        logger.info(
            "FrameProcessor initialized",
            context={
                "max_queue_size": max_queue_size,
                "command_queue_size": command_queue_size
            },
            component=self.component_name
        )

    
    def set_frame_callback(self, callback):
        """Set the callback function for frame processing."""
        self._frame_callback = callback
    
    def set_command_callback(self, callback):
        """Set the callback function for command processing."""
        self._command_callback = callback
    
    def set_capture_callback(self, callback):
        """Set the callback function for image capture requests."""
        self._capture_callback = callback
    
    def start(self):
        """Start the frame processor worker thread."""
        if self.running:
            logger.warning("FrameProcessor already running", component=self.component_name)
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        logger.info("FrameProcessor started", component=self.component_name)

    def stop(self):
        """Stop the frame processor worker thread."""
        logger.info("Stopping FrameProcessor", component=self.component_name)
        self.running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            try:
                self.worker_thread.join(timeout=2)
                logger.info("FrameProcessor stopped", component=self.component_name)
            except Exception as e:
                logger.warning(
                    f"Failed to join worker thread: {str(e)}",
                    component=self.component_name
                )

    
    def queue_frame(self, frame_data: Dict[str, Any]) -> bool:
        """
        Queue a frame for processing.
        
        Args:
            frame_data: Dictionary containing frame data and metadata
            
        Returns:
            True if successfully queued, False otherwise
        """
        try:
            self.frame_queue.put(frame_data, block=False)
            return True
        except Full:
            logger.warning("Processing queue full, dropping frame", component=self.component_name)
            return False
        except Exception as e:
            logger.error(
                "Error putting frame data into queue",
                exception=e,
                component=self.component_name
            )
            return False

    
    def queue_command(self, command_data: Dict[str, Any]) -> bool:
        """
        Queue a command for processing.
        
        Args:
            command_data: Dictionary containing command data
            
        Returns:
            True if successfully queued, False otherwise
        """
        try:
            self.command_queue.put(command_data, block=False)
            return True
        except Full:
            logger.warning(
                "Command queue full, dropping command",
                component=self.component_name
            )
            return False
        except Exception as e:
            logger.error(
                "Error putting command into queue",
                exception=e,
                component=self.component_name
            )
            return False

    
    def _process_worker(self):
        """
        Worker thread that processes frames and commands from queues.
        """
        logger.info("Frame processing worker started", component=self.component_name)
        
        while self.running:
            try:
                # Process any pending commands first (non-blocking)
                self._process_pending_commands()
                
                # Process the next available frame
                self._process_next_frame()
                
            except Exception as e:
                # Log the error but keep the worker running
                logger.error(
                    "Error in processing thread",
                    exception=e,
                    component=self.component_name
                )
                # Avoid continuous fast logging of the same error
                time.sleep(0.1)
        
        logger.info("Frame processing worker stopped", component=self.component_name)

    
    def _process_pending_commands(self):
        """Process any pending commands from the command queue."""
        try:
            command_data = self.command_queue.get_nowait()
            if self._command_callback:
                self._command_callback(command_data)
            self.command_queue.task_done()
        except Empty:
            # No commands to process, which is normal
            pass
        except Exception as e:
            logger.error(
                "Error processing command",
                exception=e,
                component=self.component_name
            )

    
    def _process_next_frame(self):
        """Process the next available frame from the queue."""
        try:
            frame_data = self.frame_queue.get(block=True, timeout=0.1)

            # Check if a 'capture_image' command has requested a capture
            if self._capture_requested.is_set():
                capture_request = self._current_capture_request
                self._capture_callback(frame_data, capture_request)
                self._current_capture_request = None
                self._capture_requested.clear()
            
            if self._frame_callback:
                self._frame_callback(frame_data)
            else:
                print(f"Processing frame: {len(frame_data)}")
            
            self.frame_queue.task_done()
            
        except Empty:
            # Queue timeout - normal behavior
            pass
        except Exception as e:
            logger.error(
                "Error processing frame",
                exception=e,
                component=self.component_name
            )
            self._current_capture_request = None
            self._capture_requested.clear()
            raise ProcessingError(
                "Frame processing failed",
                code="FRAME_PROCESSING_FAILED",
                details={"error": str(e)},
                source=self.component_name
            ) from e

    
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes for monitoring."""
        return {
            "frame_queue_size": self.frame_queue.qsize(),
            "command_queue_size": self.command_queue.qsize()
        }

    def request_capture(self, capture_request: Dict[str, str]) -> None:
        """
        Request a frame capture.
        
        Args:
            capture_request: Dictionary containing capture request parameters
        """
        self._current_capture_request = capture_request
        logger.info(
            "Capture request received",
            context=capture_request,
            component=self.component_name
        )
        self._capture_requested.set()



