"""
AWS Kinesis Video Streams Output Handler
Handles streaming video to AWS KVS using GStreamer with kvssink plugin
"""
import os
import threading
import queue
import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from typing import Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ConfigurationError

logger = get_logger()



class KVSStreamHandler():
    """
    Output handler for streaming to AWS Kinesis Video Streams
    Uses GStreamer with kvssink plugin for efficient streaming
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.component_name = "KVSOutputHandler"
        
        # Initialize GStreamer
        Gst.init(None)
        
        # Streaming state
        self.is_streaming = False
        self.pipeline = None
        self.appsrc = None
        self.main_loop = None
        self.stream_thread = None
        
        # Stream configuration
        self.stream_name = None
        self.stream_quality = "medium"
        self.duration_seconds = 240  # Default 4 minutes
        self.stream_stop_time = None
        
        # Frame queue for thread-safe frame passing
        self.frame_queue = queue.Queue(maxsize=30)
        
        # AWS configuration
        self.aws_region = config.get('cloud', {}).get('region', 'ap-northeast-1')
        self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        if not self.aws_access_key or not self.aws_secret_key:
            raise ConfigurationError(
                "AWS credentials not found in environment variables",
                code="MISSING_AWS_CREDENTIALS",
                source=self.component_name
            )
        
        # Video properties from config
        self.video_width = config.get('input', {}).get('video_width', 1280)
        self.video_height = config.get('input', {}).get('video_height', 720)
        self.fps = config.get('input', {}).get('fps', 30)
        
        # Quality profiles for encoding
        self.quality_profiles = {
            "low": {
                "bitrate": 500,  # 500 kbps
                "key-int-max": 60,
                "bframes": 0
            },
            "medium": {
                "bitrate": 1500,  # 1.5 Mbps
                "key-int-max": 60,
                "bframes": 0
            },
            "high": {
                "bitrate": 3000,  # 3 Mbps
                "key-int-max": 60,
                "bframes": 0
            }
        }
        
        logger.info(
            "KVSOutputHandler initialized",
            context={
                "aws_region": self.aws_region,
                "video_resolution": f"{self.video_width}x{self.video_height}",
                "fps": self.fps
            },
            component=self.component_name
        )
    
    def start_streaming(self, stream_name: str, duration_seconds: int = 240, 
                       stream_quality: str = "medium") -> bool:
        """
        Start streaming to KVS
        
        Args:
            stream_name: Name of the KVS stream
            duration_seconds: Duration to stream in seconds
            stream_quality: Quality profile (low/medium/high)
            
        Returns:
            bool: True if streaming started successfully
        """
        if self.is_streaming:
            logger.warning("Streaming already in progress", component=self.component_name)
            return False
        
        try:
            self.stream_name = stream_name
            self.duration_seconds = duration_seconds
            self.stream_quality = stream_quality
            self.stream_stop_time = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(seconds=duration_seconds)
            
            # Create and start GStreamer pipeline
            if not self._create_pipeline():
                return False
            
            # Start streaming thread
            self.is_streaming = True
            self.stream_thread = threading.Thread(target=self._streaming_thread)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            # Give pipeline time to start
            time.sleep(1)
            
            logger.info(
                f"Started KVS streaming",
                context={
                    "stream_name": stream_name,
                    "quality": stream_quality,
                    "duration": duration_seconds
                },
                component=self.component_name
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to start KVS streaming", exception=e, component=self.component_name)
            self.stop_streaming()
            return False

    
    def stop_streaming(self) -> bool:
        """
        Stop streaming to KVS
        
        Returns:
            bool: True if streaming stopped successfully
        """
        if not self.is_streaming:
            return True
        
        try:
            logger.info("Stopping KVS streaming", component=self.component_name)
            
            # Signal streaming thread to stop
            self.is_streaming = False
            
            # Stop pipeline
            if self.pipeline:
                self.pipeline.send_event(Gst.Event.new_eos())
                time.sleep(1)  # Give pipeline time to flush
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline = None
                self.appsrc = None
            
            # Stop main loop
            if self.main_loop:
                self.main_loop.quit()
                self.main_loop = None
            
            # Wait for thread to finish
            if self.stream_thread:
                self.stream_thread.join(timeout=5)
                self.stream_thread = None
            
            # Clear frame queue
            while not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            logger.info(f"Stopped KVS streaming to {self.stream_name}", component=self.component_name)
            return True
            
        except Exception as e:
            logger.error("Error stopping KVS stream", exception=e, component=self.component_name)
            return False
        
    def process_frame(self, frame_data: Dict[str, Any]) -> None:
        """
        Process a frame for streaming
        
        Args:
            frame_data: Dictionary containing frame and metadata
        """
        if not self.is_streaming:
            return
        
        # Check if stream duration has expired
        if self.stream_stop_time and datetime.now(ZoneInfo("Asia/Tokyo")) >= self.stream_stop_time:
            logger.info("Stream duration reached, stopping stream", component=self.component_name)
            self.stop_streaming()
            return
        
        try:
            # Add frame to queue (non-blocking)
            self.frame_queue.put(frame_data, block=False)
        except queue.Full:
            # Drop frame if queue is full
            logger.debug("Frame queue full, dropping frame", component=self.component_name)

    def _create_pipeline(self) -> bool:
        """
        Create GStreamer pipeline for KVS streaming
        
        Returns:
            bool: True if pipeline created successfully
        """
        try:
            # Get quality profile
            profile = self.quality_profiles.get(self.stream_quality, self.quality_profiles["medium"])
            
            # Create pipeline
            pipeline_str = (
                f"appsrc name=appsrc is-live=true format=3 "
                f"caps=video/x-raw,format=RGB,width={self.video_width},height={self.video_height},framerate={self.fps}/1 ! "
                f"videoconvert ! "
                f"x264enc bitrate={profile['bitrate']} key-int-max={profile['key-int-max']} "
                f"bframes={profile['bframes']} byte-stream=true tune=zerolatency speed-preset=ultrafast ! "
                f"h264parse ! "
                f"kvssink name=kvssink "
                f"stream-name=\"{self.stream_name}\" "
                f"access-key=\"{self.aws_access_key}\" "
                f"secret-key=\"{self.aws_secret_key}\" "
                f"aws-region=\"{self.aws_region}\" "
                f"framerate={self.fps} "
                f"storage-size=512"
            )
            
            logger.debug(
                "Creating GStreamer pipeline",
                context={"pipeline": pipeline_str.replace(self.aws_secret_key, "***")},
                component=self.component_name
            )
            
            self.pipeline = Gst.parse_launch(pipeline_str)
            
            # Get appsrc element
            self.appsrc = self.pipeline.get_by_name("appsrc")
            if not self.appsrc:
                raise ConfigurationError("Failed to get appsrc element", code="APPSRC_NOT_FOUND")
            
            # Set up bus watch
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_bus_message)
            
            # Start pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise ConfigurationError("Failed to start pipeline", code="PIPELINE_START_FAILED")
            
            return True
            
        except Exception as e:
            logger.error("Failed to create GStreamer pipeline", exception=e, component=self.component_name)
            return False

    def _streaming_thread(self):
        """
        Streaming thread that processes frames and manages GStreamer main loop
        """
        try:
            # Create main loop
            self.main_loop = GLib.MainLoop()
            
            # Start frame processing in separate thread
            frame_thread = threading.Thread(target=self._process_frames)
            frame_thread.daemon = True
            frame_thread.start()
            
            # Run main loop
            self.main_loop.run()
            
        except Exception as e:
            logger.error("Error in streaming thread", exception=e, component=self.component_name)
        finally:
            self.is_streaming = False

    def _process_frames(self):
        """
        Process frames from queue and push to pipeline
        """
        while self.is_streaming:
            try:
                # Get frame from queue with timeout
                frame_data = self.frame_queue.get(timeout=1.0)
                
                # Extract frame from frame_data
                frame = frame_data.get("frame")
                if frame is None:
                    continue
                
                # Convert frame to bytes
                frame_bytes = frame.tobytes()
                
                # Create GStreamer buffer
                buffer = Gst.Buffer.new_wrapped(frame_bytes)
                
                # Set timestamp
                timestamp = frame_data.get("timestamp", time.time())
                buffer.pts = int((timestamp - self._start_time) * Gst.SECOND)
                buffer.duration = int(Gst.SECOND / self.fps)
                
                # Push buffer to pipeline
                ret = self.appsrc.emit("push-buffer", buffer)
                if ret != Gst.FlowReturn.OK:
                    logger.warning(
                        f"Failed to push buffer: {ret}",
                        component=self.component_name
                    )
                
            except queue.Empty:
                # No frames available, continue
                continue
            except Exception as e:
                if self.is_streaming:  # Only log if we're still streaming
                    logger.error("Error processing frame", exception=e, component=self.component_name)

    
    def _on_bus_message(self, bus, message):
        """
        Handle GStreamer bus messages
        """
        msg_type = message.type
        
        if msg_type == Gst.MessageType.ERROR:
            err, debug_info = message.parse_error()
            logger.error(
                f"GStreamer error: {err.message}",
                context={"debug_info": debug_info},
                component=self.component_name
            )
            self.stop_streaming()
            
        elif msg_type == Gst.MessageType.WARNING:
            warn, debug_info = message.parse_warning()
            logger.warning(
                f"GStreamer warning: {warn.message}",
                context={"debug_info": debug_info},
                component=self.component_name
            )
            
        elif msg_type == Gst.MessageType.EOS:
            logger.info("End of stream reached", component=self.component_name)
            self.stop_streaming()

    def initialize_streaming(self) -> None:
        """
        Initialize streaming components
        """
        # Record start time for timestamp calculation
        self._start_time = time.time()
    
    def cleanup(self) -> None:
        """
        Clean up resources
        """
        self.stop_streaming()
        logger.info("KVSOutputHandler cleaned up", component=self.component_name)