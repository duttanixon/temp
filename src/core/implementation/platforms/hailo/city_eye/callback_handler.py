import numpy as np
import hailo
from scipy.optimize import linear_sum_assignment
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from core.interfaces.solutions.solution import ISolution
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ProcessingError, TrackingError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

@dataclass
class Detection:
    """Data class to hold detection information"""

    label: str
    track_id: int
    confidence: float
    bbox: Tuple[float, float, float, float]
    classifications: List[Tuple[str, float]]
    class_id: int
    


class VideoProcessor:
    """Handles all the video processing operations"""

    def __init__(self, gst_context):
        """
        Initialize the video processor.
        
        Args:
            gst_context: GStreamer context
        """
        self.gst_context = gst_context

    def _handle_rgb(self, map_info, width, height):
        """
        Handle RGB buffer format.
        
        Args:
            map_info: Buffer map info
            width: Frame width
            height: Frame height
            
        Returns:
            Numpy array containing the frame
        """

        # the copy() method is used to create a copy of the numpy array.
        # This is necessary because the original numpy array is created from the buffer data.
        # And it does not own the data it represents.
        # Instead, it's just a view of the buffer data.
        return np.ndarray(
            shape=(height, width, 3), dtype=np.uint8, buffer=map_info.data
        ).copy()

    @handle_errors(component="VideoProcessor")
    def _handle_nv12(self, map_info, width, height):
        """
        Handle NV12 buffer format.
        
        Args:
            map_info: Buffer map info
            width: Frame width
            height: Frame height
            
        Returns:
            Tuple of Y and UV planes
        """


        y_plane_size = width * height
        uv_plane_size = width * height // 2
        y_plane = np.ndarray(
            shape=(height, width), dtype=np.uint8, buffer=map_info.data[:y_plane_size]
        ).copy()
        uv_plane = np.ndarray(
            shape=(height // 2, width // 2, 2),
            dtype=np.uint8,
            buffer=map_info.data[y_plane_size:y_plane_size + uv_plane_size],
        ).copy()
        # originally it was y_plane_size in the map_info.data
        # since uv_plane_size was defined but not assigned, assumed that
        # uv_plane_size will in [y_plane_size:y_plane_size + uv_plane_size]
        return y_plane, uv_plane

    @handle_errors(component="VideoProcessor")
    def _handle_yuyv(self, map_info, width, height):
        """
        Handle YUYV buffer format.
        
        Args:
            map_info: Buffer map info
            width: Frame width
            height: Frame height
            
        Returns:
            Numpy array containing the frame
        """
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
        
        Raises:
            ProcessingError: If buffer mapping fails or format is unsupported

        """
        FORMAT_HANDLERS = {
            "RGB": self._handle_rgb,
            "NV12": self._handle_nv12,
            "YUYV": self._handle_yuyv,
        }

        # Map the buffer to access data
        success, map_info = buffer.map(self.gst_context.gst.MapFlags.READ)
        if not success:
            error_msg = "Could not map buffer to read"
            logger.error(error_msg, component="VideoProcessor")
            raise ProcessingError(
                error_msg,
                code="BUFFER_MAP_FAILED",
                source="VideoProcessor"
            )

        try:
            # Handle differnet format based on provided format parameter
            handler = FORMAT_HANDLERS.get(format)
            if handler is None:
                error_msg = f"Unsupported format: {format}"
                logger.error(
                    error_msg, 
                    context={"supported_formats": list(FORMAT_HANDLERS.keys())},
                    component="VideoProcessor"
                )
                raise ProcessingError(
                    error_msg,
                    code="UNSUPPORTED_FORMAT",
                    details={"format": format, "supported_formats": list(FORMAT_HANDLERS.keys())},
                    source="VideoProcessor"
                )
                
            return handler(map_info, width, height)
            
        finally:
            # Always unmap the buffer to release resources
            buffer.unmap(map_info)

    @handle_errors(component="VideoProcessor")
    def _get_caps_from_pad(self, pad: "Gst.Pad") -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Extract capabilities from GStreamer pad.
        
        Args:
            pad: GStreamer pad
            
        Returns:
            Tuple of format, width, and height, or None for each if not available
        """
        caps = pad.get_current_caps()
        if caps:
            # Extract information from the caps
            structure = caps.get_structure(0)
            if structure:
                # Extracting some common properties
                format = structure.get_value("format")
                width = structure.get_value("width")
                height = structure.get_value("height")
                
                # logger.debug(
                #     "Retrieved caps from pad", 
                #     context={
                #         "format": format,
                #         "width": width,
                #         "height": height
                #     },
                #     component="VideoProcessor"
                # )
                
                return format, width, height
                
        logger.warning("Failed to get caps from pad", component="VideoProcessor")
        return None, None, None

    def process_buffer(
        self,
        buffer: "Gst.Buffer",  # noqa: F821
        pad: "Gst.Pad",  # noqa: F821
        ) -> Optional[np.ndarray]:
        """
        Process buffer and return frame if available.
        
        Args:
            buffer: GStreamer buffer
            pad: GStreamer pad
            
        Returns:
            Numpy array containing the frame, or None if unavailable
            
        Raises:
            ProcessingError: If processing fails
        """
        format, width, height = self._get_caps_from_pad(pad)

        if None in (format, width, height):
            return None

        try:
            return self._get_numpy_from_buffer(buffer, format, width, height)
        except Exception as e:
            if not isinstance(e, ProcessingError):
                error_msg = "Error processing buffer"
                logger.error(
                    error_msg,
                    exception=e,
                    context={"format": format, "width": width, "height": height},
                    component="VideoProcessor"
                )
                raise ProcessingError(
                    error_msg,
                    code="BUFFER_PROCESSING_FAILED",
                    details={"format": format, "width": width, "height": height, "error": str(e)},
                    source="VideoProcessor"
                ) from e
            raise


    def process_detection(
        self,
        buffer: "Gst.Buffer",  # noqa: F821
        solution: "ISolution",
    ) -> List[Detection]:
        """
        Process detections from buffer.
        
        Args:
            buffer: GStreamer buffer
            solution: Solution implementation
            
        Returns:
            List of Detection objects
            
        Raises:
            ProcessingError: If detection extraction fails
        """
        try:
            # Get Region of Interest from buffer
            roi = hailo.get_roi_from_buffer(buffer)
            if roi is None:
                logger.warning("No ROI available in buffer", component="VideoProcessor")
                return []
                
            # Extract detections
            detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
            if not detections:
                logger.debug("No detections in ROI", component="VideoProcessor")
                return []

            # Process each detection
            results = []
            for detection in detections:
                # Get classifications if available
                classifications = detection.get_objects_typed(hailo.HAILO_CLASSIFICATION)
                classification_info = []

                for classification in classifications:
                    class_label = classification.get_label()
                    class_confidence = classification.get_confidence()
                    classification_info.append((class_label, class_confidence))

                # Get tracking ID if available    
                track_id = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
                if len(track_id) == 1:
                    t_id = track_id[0].get_id()
                    bbox = detection.get_bbox()
                    confidence = detection.get_confidence()

                    # Scale bounding box to frame dimensions
                    scaled_bbox = [
                            int(bbox.xmin() * solution.frame_width),
                            int(bbox.ymin() * solution.frame_height),
                            int(bbox.xmax() * solution.frame_width),
                            int(bbox.ymax() * solution.frame_height)
                        ]

                    # Create Detection object
                    results.append(
                        Detection(
                            label=detection.get_label(),
                            track_id=t_id,
                            confidence=confidence,
                            bbox=scaled_bbox,
                            classifications=classification_info,
                            class_id=detection.get_class_id(),
                        )
                    )

            return results
        except Exception as e:
            error_msg = "Error processing detections"
            logger.error(
                error_msg,
                exception=e,
                component="VideoProcessor"
            )
            raise ProcessingError(
                error_msg,
                code="DETECTION_PROCESSING_FAILED",
                details={"error": str(e)},
                source="VideoProcessor"
            ) from e

class CallbackHandler:
    """Main callback handler that orchestrates the processing pipeline"""

    def __init__(self, gst_context, solution: ISolution):
        """
        Initialize callback handler.
        
        Args:
            gst_context: GStreamer context
            solution: Solution implementation
        """
        self.solution = solution
        self.gst_context = gst_context
        self.video_processor = VideoProcessor(self.gst_context)
        logger.info("CallbackHandler initialized", component="CallbackHandler")


    def app_callback(
        self,
        pad: "Gst.Pad",  # noqa: F821
        info: "Gst.PadProbeInfo",  # noqa: F821
    ) -> "Gst.PadProbeReturn":  # noqa: F821
        """
        Main callback function for processing frames.
        
        Args:
            pad: GStreamer pad
            info: GStreamer pad probe info
            
        Returns:
            GStreamer pad probe return value
        """
        # Get buffer from probe info
        buffer = info.get_buffer()
        if buffer is None:
            logger.warning("No buffer in probe info", component="CallbackHandler")
            return self.gst_context.gst.PadProbeReturn.OK
        try:
            # Create frame data dictionary
            frame_data = {}

            # Increment frame counter in solution
            self.solution.increment_counters("frame_number")

            # Process detections
            detections = self.video_processor.process_detection(
                buffer, self.solution
            )

            # Process frame if needed
            if self.solution.use_frame:
                frame = self.video_processor.process_buffer(buffer, pad)
                if frame is not None:
                    frame_data["frame"] = frame
                    frame_data["object_meta"] = detections
                
                    # Pass frame data to solution
                    self.solution.on_frame_processed(frame_data)

                else:
                    logger.warning("Could not process frame", component="CallbackHandler")

            return self.gst_context.gst.PadProbeReturn.OK

        except Exception as e:
            error_msg = "Error in app callback"
            logger.error(
                error_msg,
                exception=e,
                component="CallbackHandler"
            )
            # Return OK to avoid blocking the pipeline
            return self.gst_context.gst.PadProbeReturn.OK


    def tracking_callback(
        self,
        pad: "Gst.Pad",  # noqa: F821
        info: "Gst.PadProbeInfo",  # noqa: F821
    ) -> "Gst.PadProbeReturn":  # noqa: F821
        """
        Callback function for tracking.
        
        Args:
            pad: GStreamer pad
            info: GStreamer pad probe info
            
        Returns:
            GStreamer pad probe return value
        """
        buffer = info.get_buffer()
        if buffer is None:
            logger.warning("No buffer in tracking probe info", component="CallbackHandler")
            return self.gst_context.gst.PadProbeReturn.OK

        try:
            # Get frame from buffer
            frame = self.video_processor.process_buffer(buffer, pad)
            if frame is None:
                logger.warning("Could not process tracking frame", component="CallbackHandler")
                return self.gst_context.gst.PadProbeReturn.OK


            # Get ROI from buffer
            roi = hailo.get_roi_from_buffer(buffer)
            if roi is None:
                logger.warning("No ROI in tracking buffer", component="CallbackHandler")
                return self.gst_context.gst.PadProbeReturn.OK
                
            # Increment tracking counter
            self.solution.increment_counters("tracking")

            # Process tracking
            frame_number = self.solution.get_frame_count("tracking")
            self._track_processor(frame, roi, frame_number)

            return self.gst_context.gst.PadProbeReturn.OK

        except Exception as e:
            error_msg = "Error in tracking callback"
            logger.error(
                error_msg,
                exception=e,
                component="CallbackHandler"
            )
            # Return OK to avoid blocking the pipeline
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
        try:
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

        except Exception as e:
            error_msg = "Error computing IoU matrix"
            logger.error(
                error_msg,
                exception=e,
                component="CallbackHandler"
            )
            
            raise TrackingError(
                error_msg,
                code="IOU_COMPUTATION_FAILED",
                details={"error": str(e)},
                source="CallbackHandler"
            ) from e



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
        try:
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

        except Exception as e:
            error_msg = "Error matching detections to tracks"
            logger.error(
                error_msg,
                exception=e,
                component="CallbackHandler"
            )
            
            raise TrackingError(
                error_msg,
                code="DETECTION_MATCHING_FAILED",
                details={"error": str(e)},
                source="CallbackHandler"
            ) from e

    def _track_processor(self, frame, roi, frame_count) ->None:
        """
        Process tracking for a frame.
        
        Args:
            frame: Video frame
            roi: Region of interest
            frame_count: Current frame count
            
        Returns:
            Dictionary of tracking results
            
        Raises:
            TrackingError: If tracking processing fails
        """
        try:
            detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
            if not detections:
                logger.debug("No detections in ROI for tracking", component="CallbackHandler")
                return {}

            # Get frame dimensions
            frame_height, frame_width = frame.shape[:2]


            # Filter out classes that are not people, bicycle, car, motorcycle, bus, truck
            valid_class_ids = {1, 2, 3, 4, 6, 8}  # Using a set is typically faster for 'in' checks
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

            # Track objects using the solution's tracker
            t_ids, t_bboxes, t_scores, t_class_ids = self.solution.tracking_manager.tracker(
                frame, bboxes, confidences, class_ids
            )
            # Assign detections to tracks
            self._match_detections_to_tracks(
                bboxes,
                filtered_detections,  # directly pass the filtered detections
                t_ids,
                t_bboxes,
            )

        except Exception as e:
            error_msg = "Error in track processor"
            logger.error(
                error_msg,
                exception=e,
                component="CallbackHandler"
            )
            
            if not isinstance(e, TrackingError):
                raise TrackingError(
                    error_msg,
                    code="TRACK_PROCESSING_FAILED",
                    details={"error": str(e)},
                    source="CallbackHandler"
                ) from e
            
            raise