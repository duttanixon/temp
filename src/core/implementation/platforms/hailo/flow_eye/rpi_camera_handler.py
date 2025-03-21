import threading
import cv2
import numpy as np
from picamera2 import Picamera2
from typing import Optional, Dict


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
        self.pipeline = pipeline
        self.width = width
        self.height = height
        self.video_format = video_format
        self.picamera_config = picamera_config
        self.running = True
        self.thread = True
        self.context = gst_context

    def start(self):
        """Start the RPi camera thread"""
        self.thread = threading.Thread(target=self._camera_thread)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop the RPi camera thread"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _camera_thread(self):
        """Main camera thread function"""
        appsrc = self.pipeline.get_by_name("app_source")
        if not appsrc:
            print("Error: Could not find app_source element")
            return

        appsrc.set_property("is-live", True)
        appsrc.set_property("format", self.context.gst.Format.TIME)

        with Picamera2() as picam2:
            if self.picamera_config is None:
                main = {"size": (1280, 720), "format": "RGB888"}
                lores = {"size": (self.width, self.height), "format": "RGB888"}
                controls = {"FrameRate": 30}
                config = picam2.create_preview_configuration(
                    main=main, lores=lores, controls=controls
                )
            else:
                config = picam2.create_preview_configuration(
                    main=self.picamera_config["main"],
                    lores=self.picamera_config["lores"],
                    controls=self.picamera_config["controls"],
                )

            picam2.configure(config)
            lores_stream = config["lores"]
            format_str = (
                "RGB" if lores_stream["format"] == "RGB888" else self.video_format
            )
            width, height = lores_stream["size"]

            appsrc.set_property(
                "caps",
                self.context.gst.Caps.from_string(
                    f"video/x-raw, format={format_str}, width={width}, height={height}, "
                    f"framerate=30/1, pixel-aspect-ratio=1/1"
                ),
            )

            picam2.start()
            frame_count = 0

            while self.running:
                frame_data = picam2.capture_array("lores")
                if frame_data is None:
                    print("Failed to capture frame")
                    break

                frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
                frame = np.asarray(frame)

                buffer = self.context.gst.Buffer.new_wrapped(frame.tobytes())
                buffer_duration = self.context.gst.util_uint64_scale_int(
                    1, self.context.gst.SECOND, 30
                )
                buffer.pts = frame_count * buffer_duration
                buffer.duration = buffer_duration

                ret = appsrc.emit("push-buffer", buffer)
                if ret != self.context.gst.FlowReturn.OK:
                    print(f"Failed to push buffer: {ret}")
                    break

                frame_count += 1
