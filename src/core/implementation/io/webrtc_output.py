from typing import Any, Dict
import time
import cv2
import numpy as np
import threading
import json
import base64
import asyncio
import uuid
from flask import Flask, Response, render_template_string, request, jsonify
from flask_cors import CORS
# aiortc is required for WebRTC functionality
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
from core.interfaces.io.output_handler import IOutputHandler
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import OutputHandlerError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class WebRTCOutputHandler(IOutputHandler):
    """Output handler with WebRTC data channel streaming for low-bandwidth scenarios"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the WebRTC output handler with configuration.

        Args:
            config: Dictionary containing output configuration.
        """
        self.use_frame = config.get("use_frame", False)
        self.config = config
        self._app = None
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self._stream_fps = config.get("streaming_fps", 2.0) # Adjusted for more real-time feel
        self._last_update_time = 0
        self._streaming_enabled = config.get("streaming", False)
        self._jpeg_quality = config.get("jpeg_quality", 50)  # Lower quality for bandwidth

        # WebRTC specific attributes
        self._clients = {}  # Store client RTCPeerConnection and DataChannel objects
        self._clients_lock = threading.Lock()
        self._asyncio_thread = None
        self._asyncio_loop = None

        logger.info(
            "WebRTCOutputHandler created",
            context={
                "streaming_enabled": self._streaming_enabled,
                "jpeg_quality": self._jpeg_quality
            },
            component="WebRTCOutputHandler"
        )

    @handle_errors(component="WebRTCOutputHandler")
    def handle_result(self, frame_data: Dict[str, Any]) -> None:
        """
        Function that's called after every frame is processed.

        Args:
            frame_data: Dictionary containing frame data and detection result
        """
        try:
            if not self._streaming_enabled:
                return
                
            object_meta = frame_data.get("object_meta", [])
            frame = frame_data.get("frame")

            if frame is not None:
                self._update_frame(frame, object_meta)
        except Exception as e:
            error_msg = "Error handling frame result"
            logger.error(error_msg, exception=e, component="WebRTCOutputHandler")
            raise OutputHandlerError(
                error_msg,
                code="FRAME_HANDLING_ERROR",
                details={"error": str(e)},
                source="WebRTCOutputHandler"
            ) from e

    def _update_frame(self, frame, object_meta):
        """Update the latest frame with rate limiting"""
        current_time = time.time()
        if (current_time - self._last_update_time) < (1.0 / self._stream_fps):
            return

        annotated_frame = self._draw_annotations(frame, object_meta)
        
        # Compress frame to JPEG with lower quality
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality])
        
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        with self._frame_lock:
            self._latest_frame = {
                'timestamp': current_time,
                'data': frame_base64,
                'width': frame.shape[1],
                'height': frame.shape[0]
            }
        
        self._last_update_time = current_time

    @handle_errors(component="WebRTCOutputHandler")
    def initialize_streaming(self) -> None:
        """Initialize the WebRTC streaming server if streaming is enabled."""
        if not self._streaming_enabled:
            logger.info("Streaming not enabled, skipping initialization", component="WebRTCOutputHandler")
            return

        try:
            self._app = Flask(__name__)
            CORS(self._app)
            self._setup_routes()

            # Start the asyncio event loop in a separate thread for WebRTC
            self._asyncio_loop = asyncio.new_event_loop()
            self._asyncio_thread = threading.Thread(target=self._start_asyncio_loop)
            self._asyncio_thread.daemon = True
            self._asyncio_thread.start()
            
            # Start the data sender coroutine
            asyncio.run_coroutine_threadsafe(self._data_sender_loop(), self._asyncio_loop)

            # Start the Flask streaming server
            host = self.config.get("streaming_host", "0.0.0.0")
            port = self.config.get("streaming_port", 7000)
            self._start_flask(host=host, port=port)
            logger.info(f"WebRTC streaming enabled at http://{host}:{port}", component="WebRTCOutputHandler")

        except Exception as e:
            error_msg = "Error initializing WebRTC streaming server"
            logger.error(error_msg, exception=e, component="WebRTCOutputHandler")
            raise OutputHandlerError(
                error_msg,
                code="STREAMING_INIT_ERROR",
                details={"error": str(e)},
                source="WebRTCOutputHandler",
                recoverable=False
            ) from e

    def _start_asyncio_loop(self):
        """Run the asyncio event loop."""
        asyncio.set_event_loop(self._asyncio_loop)
        self._asyncio_loop.run_forever()

    def _start_flask(self, host="0.0.0.0", port=7000):
        """Start the Flask server in a separate thread"""
        try:
            server_thread = threading.Thread(
                target=self._app.run,
                kwargs={"host": host, "port": port, "debug": False, "threaded": True},
            )
            server_thread.daemon = True
            server_thread.start()
        except Exception as e:
            logger.error("Failed to start Flask server", exception=e, component="WebRTCOutputHandler")
            raise

    async def _data_sender_loop(self):
        """Coroutine that periodically sends the latest frame to all clients."""
        logger.info("Starting data sender loop", component="WebRTCOutputHandler")
        while True:
            await asyncio.sleep(1.0 / self._stream_fps)
            with self._frame_lock:
                if self._latest_frame is None:
                    continue
                frame_packet = json.dumps(self._latest_frame)
            
            with self._clients_lock:
                clients_to_remove = []
                for client_id, client in self._clients.items():
                    dc = client.get("data_channel")
                    if dc and dc.readyState == "open":
                        try:
                            dc.send(frame_packet)
                        except Exception as e:
                            logger.warning(f"Failed to send to client {client_id}: {e}", component="WebRTCOutputHandler")
                    elif client.get("pc") and client["pc"].connectionState == "failed":
                         clients_to_remove.append(client_id)

                # Clean up failed clients
                for client_id in clients_to_remove:
                    logger.info(f"Removing failed client: {client_id}", component="WebRTCOutputHandler")
                    await self._clients[client_id]["pc"].close()
                    del self._clients[client_id]

    def _draw_annotations(self, frame, object_meta):
        """Draw bounding boxes and labels on frame"""
        display_frame = cv2.cvtColor(frame.copy(), cv2.COLOR_RGB2BGR)
        age_groups = {"less_than_18": "<18", "18_to_29": "18-29", "30_to_49": "30-49", "50_to_64": "50-64", "65_plus": "65+"}
        gender_groups = {"female": "f", "male": "m"}
        
        if object_meta:
            for detection in object_meta:
                try:
                    if detection.label != "person":
                        label = f"{detection.track_id} - {detection.label}: {detection.confidence:.2f}"
                    else:
                        if detection.classifications:
                            gender, _ = detection.classifications[0]
                            age, _ = detection.classifications[1]
                            gender = gender_groups.get(gender, gender)
                            age = age_groups.get(age, age)
                            label = f"{detection.track_id}:{gender}:{age}"
                        else:
                            label = f"{detection.track_id} - {detection.label}: {detection.confidence:.2f}"
                    
                    x1, y1, x2, y2 = detection.bbox
                    color = (0, 0, 255) if detection.label == "person" else (255, 0, 0)
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                    y_offset = y1 - 10 if y1 - 10 > 10 else y1 + 20
                    self.draw_label(display_frame, label, (x1, y_offset), bg_color=color)
                except Exception as e:
                    logger.error("Error drawing detection", exception=e, component="WebRTCOutputHandler")
        
        return display_frame

    def draw_label(self, frame, text, pos, bg_color=(0, 0, 0), text_color=(255, 255, 255)):
        """Draw semi-transparent background label on the image."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
        x, y = pos
        cv2.rectangle(frame, (x, y - text_size[1] - 4), (x + text_size[0], y + 4), bg_color, -1)
        cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness, cv2.LINE_AA)
        return frame

    def _setup_routes(self):
        """Set up Flask routes for the WebRTC streaming server"""
        @self._app.route("/")
        def index():
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cybercore CityEye WebRTC Stream</title>
                <style>
                    body { text-align: center; margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f0f0f0; }
                    #video-container { max-width: 1200px; margin: 20px auto; position: relative; background: #000; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
                    #canvas { max-width: 100%; border: 1px solid #ddd; display: block; margin: 0 auto; }
                    h1 { color: #333; }
                    .stats-container { display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
                    .stats-info { text-align: left; margin: 20px auto; max-width: 600px; padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
                    .error { color: #D8000C; background-color: #FFBABA; padding: 10px; border-radius: 5px; margin: 10px auto; max-width: 600px; }
                    .status { padding: 8px 15px; border-radius: 15px; display: inline-block; margin: 5px; font-weight: bold; color: white; }
                    .connected { background: #4CAF50; }
                    .disconnected { background: #f44336; }
                    .connecting { background: #FFC107; color: #333; }
                    .latency { background: #2196F3; }
                    .fps { background: #9C27B0; }
                </style>
            </head>
            <body>
                <h1>CityEye WebRTC Stream</h1>
                <div class="stats-container">
                    <span id="connection-status" class="status disconnected">Disconnected</span>
                    <span id="latency" class="status latency">Latency: -- ms</span>
                    <span id="fps" class="status fps">FPS: --</span>
                </div>
                <div id="video-container">
                    <canvas id="canvas"></canvas>
                </div>
                <div id="error" class="error" style="display: none;"></div>
                <div class="stats-info">
                    <h3>Stream Information</h3>
                    <p>Protocol: WebRTC Data Channel</p>
                    <p>Optimized for low-latency, high-performance connections.</p>
                    <p id="frame-info">Frame size: -- x --</p>
                    <p id="data-rate">Data rate: -- KB/s</p>
                </div>
                <script>
                    const canvas = document.getElementById('canvas');
                    const ctx = canvas.getContext('2d');
                    const connectionStatus = document.getElementById('connection-status');
                    const latencyElem = document.getElementById('latency');
                    const fpsElem = document.getElementById('fps');
                    const frameInfoElem = document.getElementById('frame-info');
                    const dataRateElem = document.getElementById('data-rate');
                    const errorDiv = document.getElementById('error');
                    
                    let pc;
                    let dataChannel;
                    let frameCounter = 0;
                    let lastFrameTime = performance.now();
                    let totalData = 0;

                    function setupPeerConnection() {
                        pc = new RTCPeerConnection({ iceServers: [] });

                        pc.onconnectionstatechange = () => {
                            const status = pc.connectionState;
                            connectionStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                            connectionStatus.className = 'status ' + status;
                            if (status === 'failed' || status === 'disconnected' || status === 'closed') {
                                setTimeout(connect, 3000); // Attempt to reconnect
                            }
                        };
                        
                        dataChannel = pc.createDataChannel('frames', { ordered: true, maxRetransmits: 0 });
                        dataChannel.onmessage = handleDataChannelMessage;
                        dataChannel.onopen = () => console.log('Data channel opened');
                        dataChannel.onclose = () => console.log('Data channel closed');
                        dataChannel.onerror = (err) => console.error('Data channel error:', err);
                        
                        return pc;
                    }
                    
                    function handleDataChannelMessage(event) {
                        try {
                            const frameData = JSON.parse(event.data);
                            const img = new Image();
                            img.src = 'data:image/jpeg;base64,' + frameData.data;
                            
                            img.onload = () => {
                                if (canvas.width !== frameData.width || canvas.height !== frameData.height) {
                                    canvas.width = frameData.width;
                                    canvas.height = frameData.height;
                                    frameInfoElem.textContent = `Frame size: ${frameData.width} x ${frameData.height}`;
                                }
                                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                                
                                const now = performance.now();
                                const latency = (Date.now() / 1000 - frameData.timestamp) * 1000;
                                latencyElem.textContent = `Latency: ${latency.toFixed(0)} ms`;
                                
                                // Stats calculation
                                frameCounter++;
                                totalData += event.data.length;
                                const timeDiff = now - lastFrameTime;
                                if (timeDiff >= 1000) {
                                    const fps = (frameCounter / (timeDiff / 1000)).toFixed(1);
                                    const dataRate = (totalData / 1024 / (timeDiff / 1000)).toFixed(2);
                                    fpsElem.textContent = `FPS: ${fps}`;
                                    dataRateElem.textContent = `Data rate: ${dataRate} KB/s`;
                                    frameCounter = 0;
                                    totalData = 0;
                                    lastFrameTime = now;
                                }
                            };
                        } catch(e) {
                            console.error("Error processing frame: ", e);
                        }
                    }

                    async function connect() {
                        if (pc && (pc.connectionState === 'connected' || pc.connectionState === 'connecting')) {
                            return;
                        }
                        
                        console.log("Attempting to connect...");
                        connectionStatus.textContent = 'Connecting';
                        connectionStatus.className = 'status connecting';
                        
                        pc = setupPeerConnection();
                        
                        try {
                            const offer = await pc.createOffer();
                            await pc.setLocalDescription(offer);

                            const response = await fetch('/offer', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    sdp: pc.localDescription.sdp,
                                    type: pc.localDescription.type
                                })
                            });

                            if (!response.ok) throw new Error(`Server responded with ${response.status}`);
                            
                            const answer = await response.json();
                            await pc.setRemoteDescription(new RTCSessionDescription(answer));
                        } catch (e) {
                            console.error("Connection failed:", e);
                            errorDiv.textContent = `Connection failed: ${e.message}. Retrying in 3 seconds.`;
                            errorDiv.style.display = 'block';
                            if(pc) pc.close();
                            setTimeout(connect, 3000);
                        }
                    }

                    window.onload = connect;
                </script>
            </body>
            </html>
            """)

        @self._app.route("/offer", methods=["POST"])
        def offer():
            params = request.get_json()
            offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

            # Use run_coroutine_threadsafe to interact with the asyncio loop
            future = asyncio.run_coroutine_threadsafe(self._handle_offer(offer), self._asyncio_loop)
            try:
                answer = future.result(timeout=10) # 10-second timeout
                return jsonify({"sdp": answer.sdp, "type": answer.type})
            except Exception as e:
                logger.error(f"Failed to create offer: {e}", component="WebRTCOutputHandler")
                return jsonify({"error": str(e)}), 500

    async def _handle_offer(self, offer):
        """Asynchronously handles the WebRTC offer from a client."""
        pc = RTCPeerConnection()
        client_id = f"client_{uuid.uuid4()}"

        @pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"DataChannel {channel.label} created for {client_id}", component="WebRTCOutputHandler")
            with self._clients_lock:
                self._clients[client_id]["data_channel"] = channel

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state for {client_id} is {pc.connectionState}", component="WebRTCOutputHandler")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self._cleanup_client(client_id)

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        with self._clients_lock:
            self._clients[client_id] = {"pc": pc, "data_channel": None}
            
        return pc.localDescription

    async def _cleanup_client(self, client_id):
        """Cleans up a specific client connection."""
        with self._clients_lock:
            if client_id in self._clients:
                logger.info(f"Cleaning up client {client_id}", component="WebRTCOutputHandler")
                pc = self._clients[client_id]["pc"]
                if pc.connectionState != "closed":
                    await pc.close()
                del self._clients[client_id]

    def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up WebRTCOutputHandler resources.", component="WebRTCOutputHandler")
        if self._asyncio_loop:
            # Close all client connections
            future = asyncio.run_coroutine_threadsafe(self._shutdown_clients(), self._asyncio_loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                logger.error(f"Error during client shutdown: {e}", component="WebRTCOutputHandler")
            
            # Stop the loop
            self._asyncio_loop.call_soon_threadsafe(self._asyncio_loop.stop)
            if self._asyncio_thread:
                self._asyncio_thread.join(timeout=2)
    
    async def _shutdown_clients(self):
        """Coroutine to close all active WebRTC connections."""
        with self._clients_lock:
            tasks = [self._clients[client_id]["pc"].close() for client_id in self._clients]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            self._clients.clear()
        logger.info("All WebRTC clients shut down.", component="WebRTCOutputHandler")