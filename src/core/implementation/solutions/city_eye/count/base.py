from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import numpy as np
import itertools
import cv2
import os
from collections import defaultdict

class BaseCounter():

    def get_center_box(self, box):
        return np.array([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2])

    def get_points(self, box, point_cfgs=[[1 / 2, 1 / 2]]):
        points = []
        for (x_factor, y_factor) in point_cfgs:
            points.append([box[0] + (box[2] - box[0]) * x_factor, box[1] + (box[3] - box[1]) * y_factor])
        return points
    def get_box_4points(self, box):
        # upper left, upper right, lower right, lower left
        return np.array(
            [[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]
             ])

    def get_color(self, idx):
        idx = idx * 3
        color = ((37 * idx) % 255, (17 * idx) % 255, (29 * idx) % 255)

        return color

    def check_point_in_polygon(self, point, polygon):
        point = Point(*point)
        return polygon.contains(point)

    def check_box_intersect_polygon(self, box, polygon):
        x1, y1, x2, y2 = box
        for point in [(x1, y1), (x1, y2), (x2, y1), (x2, y2)]:
            if (self.check_point_in_polygon(point, polygon)):
                return True
        return False

    def cosine_similarity(self, vec1, vec2):
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return vec1.T.dot(vec2) / (norm1 * norm2)

    def get_direction_and_count_table(self, polygons):
        # initialize direction_dict and count_table
        centroids = [list(Polygon(poly).centroid.coords)[0] for poly in polygons]
        n_xlines = len(polygons)
        direction_dict = defaultdict(lambda: {})
        for idx_1, idx_2 in itertools.combinations(range(len(centroids)), 2):
            vec = np.array([centroids[idx_2][0] - centroids[idx_1][0], centroids[idx_2][1] - centroids[idx_1][1]])
            direction_dict[idx_1][idx_2] = vec
            direction_dict[idx_2][idx_1] = -vec
        count_table = np.zeros((n_xlines + 1, n_xlines + 1, len(self.class_names)), dtype=np.uint32)
        return direction_dict, count_table

    def get_direction(self, vec, xline_idx):
        # determine direction by last box
        cosines = np.array(
            [self.cosine_similarity(vec, direct_vec) for direct_vec in self.direction_dict[xline_idx].values()])
        max_idx = np.argmax(np.abs(cosines))
        if (cosines[max_idx] > 0):
            return "in"
        return "out"

    def determine_direction_by_boxes(self, previous_boxes, current_box, xline_idx, track_id):
        # determine direction by series of boxes
        count = {"in": 0, "out": 0}
        direction = None
        for prev_box in previous_boxes:
            vec = np.array(np.array(self.get_points(current_box, self.point_cfgs)[0]) - np.array(
                self.get_points(prev_box, self.point_cfgs)[0]))
            direction = self.get_direction(vec, xline_idx)
            count[direction] += 1
        if count["in"] == count["out"]:
            return direction
        elif count["in"] > count["out"]:
            return "in"
        else:
            return "out"

    def determine_direction(self, track_info, current_box, xline_idx, track_id):
        # if direction is determined by series of boxes same as direction by last box, return direction
        if len(track_info["boxes"]) < self.frame_thresh:
            return None
        current_velocity = track_info["velocities"][-1]
        previous_boxes = track_info["boxes"][-5:]
        box_direction = self.determine_direction_by_boxes(previous_boxes, current_box, xline_idx, track_id)
        direction_by_velocity = self.get_direction(current_velocity, xline_idx)
        if box_direction == direction_by_velocity:
            return box_direction
        return None