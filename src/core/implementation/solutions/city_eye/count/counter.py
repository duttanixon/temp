import json
import numpy as np
from shapely.geometry import Point
from collections import defaultdict
from .base import BaseCounter
from typing import List, Dict, Any, DefaultDict, Optional, Tuple 
from shapely.geometry.polygon import Polygon
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import SolutionError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class Counter(BaseCounter):
    """Counter for tracking objects moving through defined zones"""
    
    def __init__(self, xlines_cfg_path:str, count_output_path:str, class_names_dict: Dict[str, List[str]], buffer_size:int = 30, frame_thresh:int=5, cos_thresh:int = 0.0, handle:bool=True):
        """
        Initialize the counter with configuration.
        Args:
            xlines_cfg_path: Path to crossing lines configuration
            count_output_path: Path to output counted results
            class_names_dict: Dictionary mapping detection types to class names
            buffer_size: Size of tracking buffer
            frame_thresh: Threshold for frame-based decisions
            cos_thresh: Cosine similarity threshold
            handle: Whether to handle detections directly
            
        Raises:
            SolutionError: If initialization fails
        """
        self.component_name = self.__class__.__name__ # For logger

        # Store initial parameters that might be needed for re-initialization
        self.initial_xlines_cfg_path = xlines_cfg_path
        self.initial_count_output_path = count_output_path
        self.initial_class_names_dict = class_names_dict.copy() # Make a copy
        self.initial_buffer_size = buffer_size
        self.initial_frame_thresh = frame_thresh
        self.initial_cos_thresh = cos_thresh
        self.initial_handle = handle
        
        # Call the main initialization logic
        self._initialize_counter_logic(
            xlines_cfg_path,
            count_output_path,
            class_names_dict,
            buffer_size,
            frame_thresh,
            cos_thresh,
            handle
        )


    def _initialize_counter_logic(self, xlines_cfg_path:str, count_output_path:str, class_names_dict: Dict[str, List[str]], buffer_size:int = 30, frame_thresh:int=5, cos_thresh:float = 0.0, handle:bool=True):
        """Helper to contain the core initialization logic, callable on initial load and on reload."""
        try:
            # Normalize class names dict to lowercase keys for consistency
            self.class_names_dict = {k.lower(): v for k, v in class_names_dict.items()}
            
            # Validate required classes
            required_classes = ['age', 'gender', 'vehicle']
            for req_class in required_classes:
                if req_class not in self.class_names_dict:
                    error_msg = f"Missing required class in class_names_dict: {req_class}"
                    logger.error(error_msg, component=self.component_name)
                    raise SolutionError(error_msg, code="MISSING_REQUIRED_CLASS", details={"required_classes": required_classes, "provided_classes": list(self.class_names_dict.keys())}, source=self.component_name)

            
            # Store class names for different detection types
            self.age_classes: List[str] = self.class_names_dict['age']
            self.gender_classes: List[str] = self.class_names_dict['gender']
            self.vehicle_classes: List[str] = self.class_names_dict['vehicle']
        
            # Create combined class names for counting        
            vehicle_class_names = [f"vehicle::{vehicle_class}" for vehicle_class in self.vehicle_classes]
            self.class_names: List[str] = [f"{gender}::{age}" for age in self.age_classes for gender in self.gender_classes]
            self.class_names.extend(vehicle_class_names)

            # Create maps for name to index and index to name
            self.name_idx_map: Dict[str, int] =  {name: idx for idx, name in enumerate(self.class_names)}
            self.idx_name_map: Dict[int, str] = {idx: name for name, idx in self.name_idx_map.items()}
        
            # Store configuration        
            self.frame_thresh: int = frame_thresh
            self.cos_thresh: float = cos_thresh
            self.handle: bool = handle
            self.buffer_size: int = buffer_size
            self.xlines_cfg_path: str = xlines_cfg_path
        
            # Load crossing lines configuration        
            self.xlines_info, self.xlines = self._load_xlines()

            # Initialize counter        
            self._init_counter()
            self.count_output_path:str = count_output_path

            # Reset these on each initialization/reload
            self.track_id_dict: Dict[str, Any] = {}
            self.finished_track_id: List[str] = []

            logger.info(
                "Counter logic initialized/re-initialized successfully",
                context={
                    "xlines_cfg_path": self.xlines_cfg_path,
                    "class_count": len(self.class_names),
                    "xlines_count": len(self.xlines),
                    "buffer_size": buffer_size
                },
                component=self.component_name
            )

        except Exception as e:
            if not isinstance(e, SolutionError):
                error_msg = "Failed to initialize counter"
                logger.error(
                    error_msg,
                    exception=e,
                    component=self.component_name
                )
                raise SolutionError(
                    error_msg,
                    code="COUNTER_INIT_FAILED",
                    details={"error": str(e)},
                    source="Counter"
                ) from e
            raise

    @handle_errors(component="Counter")
    def _load_xlines(self):
        """
        Load crossing lines configuration from self.xlines_cfg_path.
        
        Returns:
            Tuple of xlines info and polygon objects
            
        Raises:
            SolutionError: If xlines configuration cannot be loaded
        """
        try:
            logger.debug(f"Loading xlines from {self.xlines_cfg_path}", component=self.component_name)

            with open(self.xlines_cfg_path, 'r') as f:
                xlines_info = json.load(f)

            if not isinstance(xlines_info, list):
                raise SolutionError("Xlines config should be a list of polygon definitions.", code="INVALID_XLINES_FORMAT")

            # Convert xlines to Polygon objects

            xlines = [Polygon([[int(p['x']), int(p['y'])] for p in xline['content']]) for xline in xlines_info]
            return xlines_info, xlines

        except Exception as e:
            error_msg = f"Failed to load xlines from {self.xlines_cfg_path}"
            logger.error(
                error_msg,
                exception=e,
                component=self.component_name
            )
            raise SolutionError(
                error_msg,
                code="XLINES_LOAD_FAILED",
                details={"path": self.xlines_cfg_path, "error": str(e)},
                source="Counter"
            ) from e            
    
    @handle_errors(component="Counter")
    def _init_counter(self, point_cfgs: Optional[List[List[float]]] = None):
        """
        Initialize counter data structures.
        
        Args:
            point_cfgs: Point configurations for detection
        """
        if point_cfgs is None:
            point_cfgs = [[1 / 2, 1]]

        self.point_cfgs = point_cfgs

        # Initialize tracking dictionary        
        self.track_dict = defaultdict(lambda: {
            "labels": [],
            "boxes": [],
            "velocities": [],
            "last_update_frame": 0,
            "trajs": [],
            "route": ""
        })
        # Initialize direction and count tables
        self.direction_dict, self.count_table = self.get_direction_and_count_table(self.xlines)
        logger.debug("Counter data structures initialized", component=self.component_name)

    def reload_config(self, new_xlines_cfg_path: str, new_config_content: Any):
        """
        Reloads the xlines configuration for the Counter.
        The new_config_content is implicitly used because the file at new_xlines_cfg_path is updated.
        """
        logger.info(f"Reloading Counter configuration with new xlines path: {new_xlines_cfg_path}", component=self.component_name)
        
        # Call the main initialization logic with the new path.
        # Other parameters are taken from the initial setup unless they are also dynamic.
        self._initialize_counter_logic(
            xlines_cfg_path=new_xlines_cfg_path,
            count_output_path=self.initial_count_output_path, # Use initially stored or make dynamic
            class_names_dict=self.initial_class_names_dict, # Use initially stored or make dynamic
            buffer_size=self.initial_buffer_size,
            frame_thresh=self.initial_frame_thresh,
            cos_thresh=self.initial_cos_thresh,
            handle=self.initial_handle
        )

    @handle_errors(component="Counter")
    def _get_track_dict(self, frame_idx:int, detections_result: "Detection")->DefaultDict[str, Dict[str, Any]]:
        """
        Extract tracking dictionary from detection results.
        
        Args:
            frame_idx: Current frame index
            detections_result: Detection results
            
        Returns:
            Dictionary of tracking data
            
        Raises:
            SolutionError: If detection processing fails
        """

        track_dict = defaultdict(lambda: {
            "boxes": [],
            "labels": [],
            "velocities": [],
            "last_update_frame": 0,
        })

        for data in detections_result:
            track_id = data.track_id

            # Determine class label
            if data.class_id!=1:
                vehicle_class=data.label
                label_key = self.name_idx_map.get(f"vehicle::{vehicle_class}", -1)
            elif data.classifications:
                gender, age = data.classifications[0][0], data.classifications[1][0]
                label_key = self.name_idx_map.get(f"{gender}::{age}", -1)
            else:
                label_key = -1

            # Store detection data
            track_dict[track_id]["boxes"].append(data.bbox)
            track_dict[track_id]["labels"].append(label_key) 
            track_dict[track_id]["last_update_frame"] = frame_idx
        return track_dict                
    
    def _update_trajectory(self, track_id: int, frame_id: int, polygon_id: int, box: List[float] ) -> None:
        """
        Update trajectory for a tracked object.
        
        Args:
            track_id: Object track ID
            frame_id: Current frame ID
            polygon_id: Polygon ID the object is in
            box: Bounding box of the object
        """
        # Determine direction based on velocity
        direction = self.determine_direction(self.track_dict[track_id], box, polygon_id, track_id)
        last_traj = self.track_dict[track_id]["trajs"][-1] if self.track_dict[track_id]["trajs"] else None
        reset_last_out = last_traj and last_traj["in_idx"] == last_traj["out_idx"]

        if direction == "in":
            if not self.track_dict[track_id]["trajs"] \
                    or self.track_dict[track_id]["trajs"][-1]["in_idx"] != polygon_id \
                    or self.track_dict[track_id]["trajs"][-1]["found_out"]:
                self.track_dict[track_id]["trajs"].append({
                    "in_idx": polygon_id,
                    "out_idx": None,
                    "frame_th_in": frame_id,
                    "frame_th_out": None,
                    "found_out": False,
                })

        elif direction == "out":
            if not self.track_dict[track_id]["trajs"]:
                self.track_dict[track_id]["trajs"].append({
                    "in_idx": None,
                    "out_idx": polygon_id,
                    "frame_th_in": None,
                    "frame_th_out": frame_id,
                    "found_out": False,
                })
            self.track_dict[track_id]["trajs"][-1]["frame_th_out"] = frame_id
            self.track_dict[track_id]["trajs"][-1]["found_out"] = False
            self.track_dict[track_id]["trajs"][-1]["out_idx"] = polygon_id    

    def count_by_frame(self, frame_idx:int, detections_result: Dict[int, Dict[str, Any]]):
        """
        Process detections for the current frame and update counts.
        
        Args:
            frame_idx: Current frame index
            detections_result: Detection results
            
        Returns:
            Updated tracking dictionary
            
        """
        track_dict = self._get_track_dict(frame_idx, detections_result) # get the tracks of the particular frame only

        for track_id, v in track_dict.items():
            if self.track_dict[track_id]["boxes"]:
                last_center = self.get_center_box(self.track_dict[track_id]["boxes"][-1])
                velocity = np.array(self.get_center_box(v["boxes"][-1])) - np.array(last_center)
                velocity_magnitude = np.linalg.norm(velocity)
                if velocity_magnitude < 5:  # filter out small velocity
                    continue
            else:
                velocity = np.array([0, 0])

            # update track_dict
            self.track_dict[track_id]['velocities'].extend([velocity])
            self.track_dict[track_id]["labels"].extend(v["labels"])
            self.track_dict[track_id]["boxes"].extend(v["boxes"])
            self.track_dict[track_id]["last_update_frame"] = v["last_update_frame"]

            in_polygon = False
            for box in v["boxes"]:
                points = self.get_points(box, self.point_cfgs)
                for idx, polygon in enumerate(self.xlines):
                    if polygon.contains(Point(points)):
                        in_polygon = True
                        self._update_trajectory(track_id, frame_idx, idx, box)
            if not in_polygon and self.track_dict[track_id]["trajs"]:
                self.track_dict[track_id]["trajs"][-1]["found_out"] = True
        return self.track_dict
    
    def _update_count_table(self, track_id:int, traj:Optional[Dict], label_pred:int) -> Optional[str]:
        """
        Update count table with completed trajectory.
        
        Args:
            track_id: Object track ID
            traj: Trajectory information
            label_pred: Predicted label index
            
        Returns:
            Route string or None if no valid route
        """

        route = None
        if traj:
            if traj["frame_th_in"] is not None and traj["frame_th_out"] is not None:
                from_idx, to_idx = traj["in_idx"], traj["out_idx"]
                # self.count_table[from_idx, to_idx, label_pred] += 1
                route = f"{from_idx}->{to_idx}"

            elif traj["frame_th_in"] is not None and traj["frame_th_out"] is None:
                from_idx, to_idx = traj["in_idx"], len(self.xlines)
                # self.count_table[from_idx, to_idx, label_pred] += 1
                route = f"{from_idx}->loss"

            elif traj["frame_th_in"] is None and traj["frame_th_out"] is not None:
                from_idx, to_idx = len(self.xlines), traj["out_idx"]
                # self.count_table[from_idx, to_idx, label_pred] += 1
                route = f"loss->{to_idx}"

        return route

    def finish_tracklets(self, current_frame_idx: int) -> Optional[Tuple[str, str]]:
        """
        Process finished tracklets and update counts.
        
        Args:
            current_frame_idx: Current frame index
            
        Returns:
            Tuple of route and class if a tracklet was finished, None otherwise

        """

        for track_id, track_info in list(self.track_dict.items()):
            if current_frame_idx - track_info["last_update_frame"] > self.buffer_size:
                self.finished_track_id.append(track_id)
                label_list = [label for label in track_info["labels"] if label >= 0]
                if len(label_list) > 0:
                    label_pred = np.argmax(np.bincount(label_list))
                else:
                    continue
                first_in = next((traj for traj in track_info["trajs"]), None)
                last_out = next((traj for traj in reversed(track_info["trajs"])), None)                
                if first_in and last_out and first_in != last_out:
                    traj = {
                        "frame_th_in": first_in["frame_th_in"],
                        "in_idx": first_in["in_idx"],
                        "frame_th_out": last_out["frame_th_out"],
                        "out_idx": last_out["out_idx"],
                        "found_out": last_out["found_out"],
                    }
                else:
                    traj = first_in or last_out
                route = self._update_count_table(track_id, traj, label_pred)
                class_ = self.idx_name_map.get(label_pred, "unknown")
                self.track_dict[track_id]["route"] = route
                out_id = self.track_dict.pop(track_id)
                if route:
                    return route,class_
        return None