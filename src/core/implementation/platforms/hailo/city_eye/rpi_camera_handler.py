import threading
import cv2
import time
import numpy as np
from picamera2 import Picamera2
from typing import Optional, Dict, Tuple
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import HardwareError, HardwareError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()


class RPICameraHandler:
    """Handles RPi camera operations and GStreamer integration"""

    def __init__(
        self,
        pipeline,
        width: int,
        height: int,
        video_format: str,
        gst_context: "GstContext",  # noqa: F821
        picamera_config: Optional[Dict] = None,
    ):
        """
        Initialize the RPi camera handler.
        
        Args:
            pipeline: GStreamer pipeline
            width: Frame width
            height: Frame height
            video_format: Video format (e.g., 'RGB')
            gst_context: GStreamer context
            picamera_config: Custom picamera configuration (optional)
        """
        self.pipeline = pipeline
        self.width = width
        self.height = height
        self.video_format = video_format
        self.picamera_config = picamera_config
        self.running = True
        self.thread = None
        self.context = gst_context

        logger.info(
            "RPICameraHandler initialized",
            context={
                "width": width,
                "height": height,
                "format": video_format
            },
            component="RPICameraHandler"
        )
    def start(self):
        """
        Start the RPi camera thread.
        
        Raises:
            SystemError: If thread creation fails
        """
        try:
            if self.thread and self.thread.is_alive():
                logger.warning("Camera thread is already running", component="RPICameraHandler")
                return

            logger.info("Starting camera thread", component="RPICameraHandler")
            self.running = True
            self.thread = threading.Thread(target=self._camera_thread)
            self.thread.daemon = True
            self.thread.start()

           # Wait briefly to ensure thread starts properly
            time.sleep(0.1)
            
            if not self.thread.is_alive():
                error_msg = "Camera thread failed to start"
                logger.error(error_msg, component="RPICameraHandler")
                raise HardwareError(
                    error_msg,
                    code="THREAD_START_FAILED",
                    source="RPICameraHandler",
                    recoverable=False
                )
            
        except Exception as e:
            self.running = False
            
            if not isinstance(e, SystemError):
                error_msg = "Failed to start camera thread"
                logger.error(
                    error_msg,
                    exception=e,
                    component="RPICameraHandler"
                )
                raise HardwareError(
                    error_msg,
                    code="CAMERA_THREAD_ERROR",
                    details={"error": str(e)},
                    source="RPICameraHandler"
                ) from e
            raise

    def stop(self):
        """
        Stop the RPi camera thread.
        
        Raises:
            SystemError: If thread termination fails
        """
        if not self.running:
            logger.debug("Camera thread is not running", component="RPICameraHandler")
            return
            
        try:
            logger.info("Stopping camera thread", component="RPICameraHandler")
            self.running = False
            
            if self.thread:
                # Wait for thread to terminate (with timeout)
                self.thread.join(timeout=2.0)
                
                if self.thread.is_alive():
                    logger.warning("Camera thread did not terminate in time", component="RPICameraHandler")
                else:
                    logger.info("Camera thread stopped successfully", component="RPICameraHandler")
                    
                self.thread = None
        except Exception as e:
            error_msg = "Error stopping camera thread"
            logger.error(
                error_msg,
                exception=e,
                component="RPICameraHandler"
            )
            raise HardwareError(
                error_msg,
                code="THREAD_STOP_ERROR",
                details={"error": str(e)},
                source="RPICameraHandler",
                recoverable=False
            ) from e


    def _setup_camera(self) -> Tuple[Picamera2, Dict]:
        """
        Set up the PiCamera with the specified configuration.
        
        Returns:
            Tuple of Picamera2 instance and stream configuration
            
        Raises:
            HardwareError: If camera setup fails
        """
        try:
            picam2 = Picamera2()
            
            # Create camera configuration
            if self.picamera_config is None:
                main = {"size": (1280, 720), "format": "RGB888"}
                lores = {"size": (self.width, self.height), "format": "RGB888"}
                controls = {"FrameRate": 30}
                
                logger.debug(
                    "Using default camera configuration",
                    context={"main": main, "lores": lores},
                    component="RPICameraHandler"
                )
                
                config = picam2.create_preview_configuration(
                    main=main, lores=lores, controls=controls
                )
            else:
                logger.debug(
                    "Using custom camera configuration",
                    context={"config": self.picamera_config},
                    component="RPICameraHandler"
                )
                
                config = picam2.create_preview_configuration(
                    main=self.picamera_config["main"],
                    lores=self.picamera_config["lores"],
                    controls=self.picamera_config["controls"],
                )

            # Apply configuration
            picam2.configure(config)
            lores_stream = config["lores"]
            
            return picam2, lores_stream
            
        except Exception as e:
            error_msg = "Failed to set up PiCamera"
            logger.error(
                error_msg,
                exception=e,
                component="RPICameraHandler"
            )
            raise HardwareError(
                error_msg,
                code="CAMERA_SETUP_FAILED",
                details={"error": str(e)},
                source="RPICameraHandler"
            ) from e

    def _camera_thread(self) -> None:
        """
        Main camera thread function that captures frames and pushes them to the pipeline.
        """
        logger.debug("Camera thread started", component="RPICameraHandler")
        
        # Get the appsrc element from the pipeline
        appsrc = self.pipeline.get_by_name("app_source")
        if not appsrc:
            logger.error("Could not find app_source element in pipeline", component="RPICameraHandler")
            return

        # Configure appsrc
        appsrc.set_property("is-live", True)
        appsrc.set_property("format", self.context.gst.Format.TIME)
        
        try:
            # Set up camera
            picam2, lores_stream = self._setup_camera()
            
            # Get format and dimensions
            format_str = "RGB" if lores_stream["format"] == "RGB888" else self.video_format
            width, height = lores_stream["size"]
            
            # Set appsrc caps
            caps_str = (
                f"video/x-raw, format={format_str}, width={width}, height={height}, "
                f"framerate=30/1, pixel-aspect-ratio=1/1"
            )
            
            logger.debug(
                "Setting appsrc caps",
                context={"caps": caps_str},
                component="RPICameraHandler"
            )
            
            appsrc.set_property(
                "caps",
                self.context.gst.Caps.from_string(caps_str)
            )
            
            # Start camera
            picam2.start()
            logger.info("PiCamera started successfully", component="RPICameraHandler")
            
            frame_count = 0
            last_log_time = time.time()
            frames_since_log = 0
            
            # Main capture loop
            while self.running:
                try:
                    # Capture frame
                    frame_data = picam2.capture_array("lores")
                    if frame_data is None:
                        logger.warning("Failed to capture frame, retrying", component="RPICameraHandler")
                        time.sleep(0.033)  # ~30 fps
                        continue
                        
                    # Convert frame to RGB if needed
                    frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
                    frame = np.asarray(frame)
                    
                    # Create GStreamer buffer
                    buffer = self.context.gst.Buffer.new_wrapped(frame.tobytes())
                    
                    # Set buffer timestamp and duration
                    buffer_duration = self.context.gst.util_uint64_scale_int(
                        1, self.context.gst.SECOND, 30
                    )
                    buffer.pts = frame_count * buffer_duration
                    buffer.duration = buffer_duration
                    
                    # Push buffer to appsrc
                    ret = appsrc.emit("push-buffer", buffer)
                    if ret != self.context.gst.FlowReturn.OK:
                        logger.warning(
                            f"Failed to push buffer: {ret}",
                            component="RPICameraHandler"
                        )
                        
                    frame_count += 1
                    frames_since_log += 1
                    
                    # Log FPS occasionally
                    current_time = time.time()
                    time_elapsed = current_time - last_log_time
                    if time_elapsed > 60.0:  # Log every 10 seconds
                        fps = frames_since_log / time_elapsed
                        logger.debug(
                            f"Camera capture rate: {fps:.2f} FPS",
                            component="RPICameraHandler"
                        )
                        last_log_time = current_time
                        frames_since_log = 0
                        
                except Exception as e:
                    logger.error(
                        "Error capturing frame",
                        exception=e,
                        component="RPICameraHandler"
                    )
                    time.sleep(0.1)  # Brief delay before retrying
            
            # Clean up
            try:
                picam2.stop()
                logger.info("PiCamera stopped", component="RPICameraHandler")
            except Exception as e:
                logger.warning(
                    "Error stopping PiCamera",
                    exception=e,
                    component="RPICameraHandler"
                )
                
        except Exception as e:
            logger.error(
                "Fatal error in camera thread",
                exception=e,
                component="RPICameraHandler"
            )
            
            # Set running to False to prevent restart attempts
            self.running = False
            
            # Send EOS to pipeline to prevent hanging
            try:
                if appsrc:
                    logger.debug("Sending EOS to pipeline", component="RPICameraHandler")
                    appsrc.emit("end-of-stream")
            except Exception as eos_error:
                logger.warning(
                    "Error sending EOS to pipeline",
                    exception=eos_error,
                    component="RPICameraHandler"
                )