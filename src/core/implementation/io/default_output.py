from typing import Any, Dict
import time
import cv2
import threading
from flask import Flask, Response, render_template_string
from core.interfaces.io.output_handler import IOutputHandler
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import OutputHandlerError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class DefaultOutputHandler(IOutputHandler):
    """Write to database with web streaming capabilitiers"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the default output handler with configuration.

        Args:
            config: Dictionary containing output configuration.
        """
        self.use_frame = config.get("use_frame", False)
        self.config = config
        self._app = None
        self._latest_frame = None
        self._frame_lock = None
        self._stream_fps = None
        self._last_update_time = 0
        self._streaming_enabled = config.get("streaming", False)
        
        logger.info(
            "DefaultOutputHandler created",
            context={"streaming_enabled": self._streaming_enabled},
            component="DefaultOutputHandler"
        )

    @handle_errors(component="DefaultOutputHandler")
    def handle_result(self, frame_data: Dict[str, Any]) -> None:
        """
        Function that's called after every frame is processed.

        Args:
            frame_data: Dictionary containing frame data and detection and classification result
        
        Raises:
            OutputHandlerError: If there si an error handling the result
        """
        try:
            object_meta = frame_data.get("object_meta", [])
            frame = frame_data.get("frame")

            # update the streamer with the latest frame and bounding boxes
            if frame is not None and self._streaming_enabled:
                self._streamer_update_frame(frame, object_meta)
        except Exception as e:
            error_msg = "Error handling frame result"
            logger.error(
                error_msg,
                exception=e,
                component="DefaultOutputHandler"
            )
            raise OutputHandlerError(
                error_msg,
                code="FRAME_HANDLING_ERROR",
                details={"error": str(e)},
                source="DefaultOutputHandler"
            ) from e

    @handle_errors(component="DefaultOutputHandler")
    def initialize_streaming(self) -> None:
        """
        Initialize the streaming server if streaming is enabled.

        Raises:
            OutputHandlerError: If there's an error initializing streaming
        """

        if not self._streaming_enabled:
            logger.info("Streaming not enabled, skipping initialization", component="DefaultOutputHandler")
            return

        try:
            self._app = Flask(__name__)
            self._latest_frame = None
            self._frame_lock = threading.Lock()
            self._stream_fps = self.config.get(
                "streaming_fps", 0.5
            )  # Default to 0.5 fps (1 frame every 2 seconds)
            self._last_update_time = 0
            self._setup_routes()
            # Start the streaming server
            host = self.config.get("streaming_host", "0.0.0.0")
            port = self.config.get("streaming_port", 7000)
            self._start(host=host, port=port)
            logger.info(f"Frame streaming enabled at http://{host}:{port}", component="DefaultOutputHandler")
    
        except Exception as e:
            error_msg = "Error initializing streaming server"
            logger.error(
                error_msg,
                exception=e,
                context={"host": self.config.get("streaming_host"), "port": self.config.get("streaming_port")},
                component="DefaultOutputHandler"
            )
            raise OutputHandlerError(
                error_msg,
                code="STREAMING_INIT_ERROR",
                details={"error": str(e)},
                source="DefaultOutputHandler",
                recoverable=False
            ) from e

    def _start(self, host="0,0,0,0", port=7000):

        """Start the streaming server in a separate thread

        Raises:
            Raise Error which in returns raises Error the caller function
        """
        try:
            server_thread = threading.Thread(
                target=self._app.run,
                kwargs={"host": host, "port": port, "debug": False, "threaded": True},
            )
            server_thread.daemon = True
            server_thread.start()
            logger.info(f"Streaming server started at http://{host}:{port}")
            return server_thread
        
        except Exception as e:
            logger.error(
                "Failed to start streaming server",
                exception=e,
                context={"host":host, "port": port},
                component="DefaultOutputHandler"
            )
            raise

    def _generate_frames(self):
        """Generator function for streaming frames.
        
        Yields:
            Frame data in the format expected by the streaming protocol
        """
        while True:
            # Control the streaming frame rate
            time.sleep(1.0 / self._stream_fps)

            with self._frame_lock:
                if self._latest_frame is None:
                    continue
                
                try:
                    # Convert the frame to JPEG
                    _, buffer = cv2.imencode(".jpg", self._latest_frame)
                    frame_bytes = buffer.tobytes()
                except Exception as e:
                    logger.error("Error encoding frame", exception=e, component="DefaultOutputHandler")
                    continue

            # Yield the frame in the format expected by the streaming protocol
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

    def draw_label(self, frame, text, pos, bg_color=(0,0,0), text_color=(255,255,255)):
        """Draw semi-transparent background label on the image."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
        x, y = pos
        # Draw rectangle background
        cv2.rectangle(frame, (x, y-text_size[1]), (x+text_size[0], y+4), bg_color, -1)
        # Draw text
        cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
        return frame

    def _streamer_update_frame(self, frame, object_meta):
        """
        Update the latest frame with optional bouding boxes.

        Args:
            frame: The frame to update
            object_meta: Object metadata with detection information
        """
        current_time = time.time()
        time_since_update = current_time - self._last_update_time

        # limit updates to our target FPS (time_sice_update >=1.0/self._stream_fps)
        if time_since_update >= 1.0 / self._stream_fps:
            try:
                # Make a copy of the frame to avoid race condition
                # display_frame = cv2.cvtColor(frame.copy(), cv2.COLOR_RGB2BGR)
                display_frame = frame.copy()

                with self._frame_lock:
                    self._latest_frame = display_frame
                    self._last_update_time = current_time
            except Exception as e:
                logger.error("Error updating frame for streaming", exception=e, component="DefaultOutputHandler")


    def _setup_routes(self):
        """Set up Flask routes for the streaming server"""
        @self._app.route("/")
        def index():
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cybercore CityEye Stream</title>
                <style>
                    body { text-align: center; margin: 0; padding: 20px; font-family: Arial, sans-serif; }
                    #stream { max-width: 100%; border: 1px solid #ddd; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    h1 { color: #333; }
                    .stats { text-align: left; margin: 20px auto; max-width: 600px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>CityEye Stream (0.5 FPS)</h1>
                    <img id="stream" src="/video_feed" />
                    <div class="stats">
                        <h3>Live Statistics</h3>
                        <p>Frame rate limited to 1 frame per 2 seconds for streaming</p>
                    </div>
                </div>
            </body>
            </html>
            """)

        @self._app.route("/video_feed")
        def video_feed():
            return Response(
                self._generate_frames(),
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )