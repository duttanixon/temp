"""
Tracking manager module for CityEye solution.
Handles object tracking and counting operations.
"""
import threading
from typing import Dict, Any, Optional

from core.implementation.solutions.city_eye.bytetrack.mc_bytetrack import MultiClassByteTrack
from core.implementation.solutions.city_eye.count.counter import Counter
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import TrackingError, SolutionError

logger = get_logger()


class TrackingManager:
    """Manages object tracking and counting operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the tracking manager.
        
        Args:
            config: Configuration for tracking and counting
        """
        self.component_name = self.__class__.__name__
        self.config = config
        
        # Initialize counters and lock
        self.counters = {"tracking": 0, "attr": 0, "frame_number": 0}
        self.counters_lock = threading.Lock()
        # Class names for counting
        self.class_names_dict = {
            'gender': ['male', 'female'],
            'age': ['less_than_18', '18_to_29', '30_to_49', '50_to_64', '65_plus'],
            'vehicle': ['bicycle', 'car', 'bus', 'truck', 'motorcycle']
        }

        # Initialize tracker
        self._initialize_tracker()

        # Initialize counter
        self._initialize_counter()

        logger.info("TrackingManager initialized", component=self.component_name)

    def _initialize_tracker(self):
        """Initialize ByteTrack tracker."""
        try:
            self.tracker = MultiClassByteTrack(
                fps=30,
                track_thresh=0.4,
                track_buffer=30,
                match_thresh=0.75,
                min_box_area=300,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize tracker",
                exception=e,
                component=self.component_name
            )
            raise

    def _initialize_counter(self):
        """Initialize Counter for object counting."""
        try:
            self.xlines_cfg_path = self.config.get("xlines_cfg_path")
            self.count_output_path = self.config.get("count_output_path")
            
            if not self.xlines_cfg_path:
                raise ValueError("xlines_cfg_path not provided in config")
            
            self.counter = Counter(
                self.xlines_cfg_path,
                self.count_output_path,
                self.class_names_dict
            )

        except Exception as e:
            logger.error(
                "Failed to initialize counter",
                exception=e,
                component=self.component_name
            )
            raise SolutionError(
                "Failed to initialize Counter",
                code="COUNTER_INIT_FAILED",
                details={"error": str(e)},
                source=self.component_name
            ) from e


    def process_frame_for_counting(self, frame_number: int, 
                                  object_meta: Dict[int, Dict[str, Any]]) -> Optional[Dict]:
        """
        Process frame data for counting.
        
        Args:
            frame_number: Current frame number
            object_meta: Detection metadata for objects in frame
            
        Returns:
            Frame result with counting data or None
        """
        try:
            # Process counting for this frame
            self.counter.count_by_frame(frame_number, object_meta)
            
            # Check if any tracklets finished
            frame_result = self.counter.finish_tracklets(frame_number)
            
            return frame_result
            
        except Exception as e:
            logger.error(
                "Error in counting module",
                exception=e,
                context={"frame_number": frame_number},
                component=self.component_name
            )
            return None




    def get_tracker(self) -> MultiClassByteTrack:
        """Get the tracker instance."""
        return self.tracker

    def get_counter(self) -> Counter:
        """Get the counter instance."""
        return self.counter
    
    def get_all_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        with self.counters_lock:
            return self.counters.copy()

    def increment_counter(self, counter_type: str) -> None:
        """
        Increment a specific counter safely with locking.
        
        Args:
            counter_type: Counter to increment
        """
        with self.counters_lock:
            if counter_type in self.counters:
                self.counters[counter_type] += 1
            else:
                logger.error(
                    f"Counter type {counter_type} not recognized",
                    component=self.component_name
                )

    def get_counter_value(self, counter_type: str) -> Optional[int]:
        """
        Get the current value of a specific counter.
        
        Args:
            counter_type: Counter to get
            
        Returns:
            Current counter value or None if counter doesn't exist
        """
        with self.counters_lock:
            return self.counters.get(counter_type)