import numpy as np
import hailo
from scipy.optimize import linear_sum_assignment
from typing import Tuple, Optional, List
from dataclasses import dataclass
from core.interfaces.solutions.solution import ISolution


@dataclass
class Detection:
    """Data class to hold detection information"""

    label: str
    track_id: int
    confidence: float
    bbox: Tuple[float, float, float, float]
    classifications: List[Tuple[str, float]]


class VideoProcessor:
    """Handles all the video processing operations"""

    def __init__(self, gst_context):
        self.gst_context = gst_context

    def _handle_rgb(self, map_info, width, height):
        # the copy() method is used to create a copy of the numpy array.
        # This is necessary because the original numpy array is created from the buffer data.
        # And it does not own the data it represents.
        # Instead, it'sn just a view of the buffer data.
        return np.ndarray(
            shape=(height, width, 3), dtype=np.uint8, buffer=map_info.data
        ).copy()

    def _handle_nv12(self, map_info, width, height):
        y_plane_size = width * height
        uv_plane_size = width * height // 2
        y_plane = np.ndarray(
            shape=(height, width), dtype=np.uint8, buffer=map_info.data[:y_plane_size]
        ).copy()
        uv_plane = np.ndarray(
            shape=(height // 2, width // 2, 2),
            dtype=np.uint8,
            buffer=map_info.data[uv_plane_size:],
        ).copy()
        # originally it was y_plane_size in the map_info.data
        # since uv_plane_size was defined but not assigned, assumed that
        # uv_plane_size will in map_info.data[y_plane_size:]
        return y_plane, uv_plane

    def _handle_yuyv(self, map_info, width, height):
        return np.ndarray(
            shape=(height, width, 2), dtype=np.uint8, buffer=map_info.data
        ).copy()

    def _get_numpy_from_buffer(self, buffer, format, width, height):
        """
        Converts a GstBuffer to a numpy array based on provided format, width, and height.

        Args:
            buffer (GstBuffer): The GStreamer Buffer to convert.
            format (str): The video format ('RGB', 'NV12', 'YUYV', etc.).
            width (int): The width of the video frame.
            height (int): The height of the video frame.

        Returns:
            np.ndarray: A numpy array representing the buffer's data, or a tuple of arrays for certain formats.
        """
        FORMAT_HANDLERS = {
            "RGB": self._handle_rgb,
            "NV12": self._handle_nv12,
            "YUYV": self._handle_yuyv,
        }

        # Map the buffer to access data
        success, map_info = buffer.map(self.gst_context.gst.MapFlags.READ)
        if not success:
            raise ValueError("Could not map buffer to read")

        try:
            # Handle differnet format based on provided format parameter
            handler = FORMAT_HANDLERS.get(format)
            if handler is None:
                raise ValueError(f"Unsupported format: {format}")
            return handler(map_info, width, height)
        finally:
            buffer.unmap(map_info)

    def _get_caps_from_pad(self, pad: "Gst.Pad"):  # noqa: F821
        caps = pad.get_current_caps()
        if caps:
            # We can now extract information from the caps
            structure = caps.get_structure(0)
            if structure:
                # Extracting some common properties
                format = structure.get_value("format")
                width = structure.get_value("width")
                height = structure.get_value("height")
                return format, width, height
        else:
            return None, None, None

    def process_buffer(
        self,
        buffer: "Gst.Buffer",  # noqa: F821
        pad: "Gst.Pad",  # noqa: F821
    ) -> Optional[np.ndarray]:
        """Processes buffer and returns frame if availble"""
        format, width, height = self._get_caps_from_pad(pad)
        if None in (format, width, height):
            return None

        return self._get_numpy_from_buffer(buffer, format, width, height)

    def process_detection(
        self,
        buffer: "Gst.Buffer",  # noqa: F821
        width: int,
        height: int,
    ) -> List[Detection]:
        """Process detections from buffer"""
        roi = hailo.get_roi_from_buffer(buffer)
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
        results = []
        for detection in detections:
            classifications = detection.get_objects_typed(hailo.HAILO_CLASSIFICATION)
            classification_info = []
            track_id = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            bbox = detection.get_bbox()
            for classification in classifications:
                class_label = classification.get_label()
                class_confidence = classification.get_confidence()
                classification_info.append((class_label, class_confidence))
            if len(track_id) == 1:
                results.append(
                    Detection(
                        label=detection.get_label(),
                        track_id=track_id[0].get_id(),
                        confidence=detection.get_confidence(),
                        bbox=[
                            int(bbox.xmin() * width),
                            int(bbox.ymin() * height),
                            int(bbox.xmax() * width),
                            int(bbox.ymax() * height),
                        ],
                        classifications=classification_info,
                    )
                )

        return results


class CallbackHandler:
    """Main callback handler that orchestrates the processing pipeline"""

    def __init__(self, gst_context, solution: ISolution):
        self.solution = solution
        self.gst_context = gst_context
        self.video_processor = VideoProcessor(self.gst_context)
        self._frame_count = 0

    def app_callback(
        self,
        pad: "Gst.Pad",  # noqa: F821
        info: "Gst.PadProbeInfo",  # noqa: F821
    ) -> "Gst.PadProbeReturn":  # noqa: F821
        """Main callback function for processing frames"""
        # Get buffer
        frame_data = {}
        buffer = info.get_buffer()
        if buffer is None:
            return self.gst_context.gst.PadProbeReturn.OK

        # Process frame if needed
        frame = None
        self.solution.increment_counters("output")
        # Process detections
        detections = self.video_processor.process_detection(
            buffer, self.solution.frame_width, self.solution.frame_height
        )
        if self.solution.use_frame:
            frame = self.video_processor.process_buffer(buffer, pad)
            frame_data["frame"] = frame
        frame_data["object_meta"] = detections
        self.solution.on_frame_processed(frame_data)

        return self.gst_context.gst.PadProbeReturn.OK

    def tracking_callback(
        self,
        pad: "Gst.Pad",  # noqa: F821
        info: "Gst.PadProbeInfo",  # noqa: F821
    ) -> "Gst.PadProbeReturn":  # noqa: F821
        """Callback function for tracking"""
        buffer = info.get_buffer()
        if buffer is None:
            return self.gst_context.gst.PadProbeReturn.OK
        frame = self.video_processor.process_buffer(buffer, pad)
        roi = hailo.get_roi_from_buffer(buffer)
        self.solution.increment_counters("tracking")
        if frame is not None:
            self._track_processor(frame, roi, self.solution.get_frame_count("tracking"))
        return self.gst_context.gst.PadProbeReturn.OK

    # Helper function to classify gender
    def _classify_gender(self, attribute_value):
        """Classify gender based on attribute value."""
        if attribute_value > 0.56:
            return "male"
        elif attribute_value < 0.56:
            return "female"
        return "unknown"

    # Helper function to classify age group
    def _classify_age(self, attributes):
        """Classify age group based on attribute values."""
        age_groups = ["young", "middle", "middle", "senior"]
        max_index = np.argmax(attributes[:4])
        max_confidence = attributes[max_index]
        return (
            (age_groups[max_index], max_confidence)
            if max_confidence > 0.55
            else ("unknown", 0.0)
        )

    def _compute_iou_matrix(self, bboxes, t_bboxes):
        """
        Compute IoU matrix between two sets of bounding boxes efficiently.

        Args:
            bboxes (ndarray): First set of bounding boxes (N x 4)
            t_bboxes (ndarray): Second set of bounding boxes (M x 4)

        Returns:
            ndarray: Matrix of IoU values (N x M)
        """
        # Convert inputs to float32 for better performance
        bboxes = np.asarray(bboxes).reshape(-1, 4)
        t_bboxes = np.asarray(t_bboxes).reshape(-1, 4)
        # Extract coordinates
        x1_min, y1_min, x1_max, y1_max = (
            bboxes[:, 0],
            bboxes[:, 1],
            bboxes[:, 2],
            bboxes[:, 3],
        )
        x2_min, y2_min, x2_max, y2_max = (
            t_bboxes[:, 0],
            t_bboxes[:, 1],
            t_bboxes[:, 2],
            t_bboxes[:, 3],
        )
        # Compute intersection
        inter_x_min = np.maximum(
            x1_min[:, None], x2_min
        )  # Broadcasting for pairwise comparison
        inter_y_min = np.maximum(y1_min[:, None], y2_min)
        inter_x_max = np.minimum(x1_max[:, None], x2_max)
        inter_y_max = np.minimum(y1_max[:, None], y2_max)
        inter_width = np.maximum(0, inter_x_max - inter_x_min)
        inter_height = np.maximum(0, inter_y_max - inter_y_min)
        inter_area = inter_width * inter_height
        # Compute areas
        area1 = (x1_max - x1_min) * (y1_max - y1_min)  # Areas of bboxes
        area2 = (x2_max - x2_min) * (y2_max - y2_min)  # Areas of t_bboxes
        # Compute union
        union_area = area1[:, None] + area2 - inter_area
        # Compute IoU and return the inverted IoU matrix
        iou_matrix = 1 - inter_area / np.maximum(union_area, 1e-6)
        return iou_matrix

    def _match_detections_to_tracks(
        self, bboxes, detection_list, t_ids, t_bboxes, iou_thresh=0.8
    ):
        """Match detections to tracking IDs and update results.

        This optimized implementation maintains the same logic as the original while
        improving performance through vectorized operations and reduced memory allocations.

        Args:
            bboxes (ndarray): Detected bounding boxes (N x 4).
            detection_list (list): The corresponding detection objects.
            t_ids (ndarray): Track IDs predicted by tracker (M x 1).
            t_bboxes list: Bounding boxes predicted by tracker (M x 4).
            t_scores (ndarray): Confidence scores from tracker (M x 1).
            iou_thresh (float): IoU threshold for accepting a match.
        """
        # Check if there are any tracking bboxes
        if len(t_bboxes) == 0:
            return  # Exit if no tracking bboxes

        # Compute IoU matrix and get matches using the Hungarian algorithm
        t_bboxes = np.asarray(t_bboxes)
        iou_matrix = self._compute_iou_matrix(bboxes, t_bboxes)
        row_ind, col_ind = linear_sum_assignment(iou_matrix)

        # Filter matches based on IoU threshold in a vectorized way
        valid_matches = iou_matrix[row_ind, col_ind] < iou_thresh
        row_ind = row_ind[valid_matches]
        col_ind = col_ind[valid_matches]

        # Process matches and update detections
        for d, t in zip(row_ind, col_ind):
            detection = detection_list[d]
            t_id = int(t_ids[t])

            # Add unique ID to detection
            detection.add_object(hailo.HailoUniqueID(t_id))

    def _track_processor(self, frame, roi, frame_count):
        detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
        frame_height, frame_width = frame.shape[:2]
        # Filter out classes that are not people, bicycle, car, motorcycle, bus, truck
        valid_class_ids = {
            1,
            2,
            3,
            4,
            6,
            8,
        }  # Using a set is typically faster for 'in' checks
        filtered_detections = []
        for det in detections:
            if det.get_class_id() in valid_class_ids:
                filtered_detections.append(det)
            else:
                # Remove unwanted detections from ROI
                roi.remove_object(det)
        # If no valid detections left, return
        if not filtered_detections:
            return {}

        # Pre-allocate arrays for bboxes, confidences, and class_ids
        num_detections = len(filtered_detections)
        bboxes = np.zeros((num_detections, 4), dtype=np.int32)
        confidences = np.zeros(num_detections, dtype=np.float32)
        class_ids = np.zeros(num_detections, dtype=np.int32)

        # Fill the arrays
        for i, det in enumerate(filtered_detections):
            x_min = max(
                0, min(int(det.get_bbox().xmin() * frame_width), frame_width - 1)
            )
            y_min = max(
                0, min(int(det.get_bbox().ymin() * frame_height), frame_height - 1)
            )
            x_max = max(
                0, min(int(det.get_bbox().xmax() * frame_width), frame_width - 1)
            )
            y_max = max(
                0, min(int(det.get_bbox().ymax() * frame_height), frame_height - 1)
            )

            bboxes[i] = [x_min, y_min, x_max, y_max]
            confidences[i] = det.get_confidence()
            class_ids[i] = det.get_class_id()

        # Track objects
        t_ids, t_bboxes, t_scores, t_class_ids = self.solution.tracker(
            frame, bboxes, confidences, class_ids
        )
        # Assign detections to tracks
        self._match_detections_to_tracks(
            bboxes,
            filtered_detections,  # directly pass the filtered detections
            t_ids,
            t_bboxes,
        )
