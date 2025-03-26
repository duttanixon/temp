import json
import numpy as np
from shapely.geometry import Point
from collections import defaultdict
from .base import BaseCounter
from typing import List, Dict, Any, DefaultDict, Optional
from shapely.geometry.polygon import Polygon

class Counter(BaseCounter):
    def __init__(self, xlines_cfg_path:str, count_output_path:str, class_names_dict: Dict[str, List[str]], buffer_size:int = 30, frame_thresh:int=5, cos_thresh:int = 0.0, handle:bool=True):
        self.class_names_dict = {k.lower(): v for k, v in class_names_dict.items()}
        assert ('age' in self.class_names_dict and 'gender' in self.class_names_dict and 'vehicle' in self.class_names_dict)
        self.age_classes: List[str] = self.class_names_dict['age']
        self.gender_classes: List[str] = self.class_names_dict['gender']
        self.vehicle_classes: List[str] = self.class_names_dict['vehicle']
        vehicle_class_names = [f"vehicle::{vehicle_class}" for vehicle_class in self.vehicle_classes]
        self.class_names: List[str] = [f"{gender}::{age}" for age in self.age_classes for gender in self.gender_classes]
        self.class_names.extend(vehicle_class_names)
        self.name_idx_map: Dict[str, int] =  {name: idx for idx, name in enumerate(self.class_names)}
        self.idx_name_map:Dict[str, int] = {idx: name for name, idx in self.name_idx_map.items()}
        self.frame_thresh: int = frame_thresh
        self.cos_thresh: float = cos_thresh
        self.handle: bool = handle
        self.track_id_dict: Dict[str, Any] = {}
        self.finished_track_id: List[str] = []
        self.buffer_size: int = buffer_size
        self.xlines_cfg_path: str = xlines_cfg_path
        self.xlines_info, self.xlines = self._load_xlines()
        self._init_counter()
        self.count_output_path:str = count_output_path
        self.saved_data = {}

    def _load_xlines(self):
        print(self.xlines_cfg_path)
        with open(self.xlines_cfg_path, 'r') as f:
            xlines_info = json.load(f)
        xlines = [Polygon([[int(p['x']), int(p['y'])] for p in xline['content']]) for xline in xlines_info]
        return xlines_info, xlines
    
    def _init_counter(self, point_cfgs:list=None):
        if point_cfgs is None:
            point_cfgs = [[1 / 2, 1]]
        self.point_cfgs = point_cfgs
        self.track_dict = defaultdict(lambda: {
            "labels": [],
            "boxes": [],
            "velocities": [],
            "last_update_frame": 0,
            "trajs": [],
            "route": ""
        })
        self.direction_dict, self.count_table = self.get_direction_and_count_table(self.xlines)

    def _get_track_dict(self, frame_idx:int, detections_result: "Detection")->DefaultDict[str, Dict[str, Any]]:
        track_dict = defaultdict(lambda: {
            "boxes": [],
            "labels": [],
            "velocities": [],
            "last_update_frame": 0,
        })
        for data in detections_result:
            track_id = data.track_id
            if data.class_id!=1:
                vehicle_class=data.label
                label_key = self.name_idx_map.get(f"vehicle::{vehicle_class}", -1)
            elif data.classifications:
                gender, age = data.classifications[0][0], data.classifications[1][0]
                label_key = self.name_idx_map.get(f"{gender}::{age}", -1)
            else:
                label_key = -1
            track_dict[track_id]["boxes"].append(data.bbox)
            track_dict[track_id]["labels"].append(label_key) 
            track_dict[track_id]["last_update_frame"] = frame_idx
        return track_dict                
    
    def _update_trajectory(self, track_id: int, frame_id: int, polygon_id: int, box: List[float] ) -> None:
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

    def finish_tracklets(self, current_frame_idx: int) -> Dict[str, str]:
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
                    self.saved_data[str(track_id)] = route
                    print(route,class_)
        return self.saved_data