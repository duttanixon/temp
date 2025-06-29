import os


def get_source_type(input_source):
    # This function will return the source type based on the input source
    # return values can be "file", "mipi" or "usb"
    if input_source.startswith("/dev/video"):
        return "usb"
    elif input_source.startswith("rpi"):
        return "rpi"
    elif input_source.startswith(
        "libcamera"
    ):  # Use libcamerasrc element, not suggested
        return "libcamera"
    elif input_source.startswith("0x"):
        return "ximage"
    elif input_source.startswith("rtsp://") or input_source.startswith("rtsps://"):
        return "rtsp"
    elif input_source.startswith("http://") or input_source.startswith("https://"):
        return "http"
    else:
        return "file"


def get_camera_resulotion(video_width=640, video_height=640):
    # This function will return a standard camera resolution based on the video resolution required
    # Standard resolutions are 640x480, 1280x720, 1920x1080, 3840x2160
    # If the required resolution is not standard, it will return the closest standard resolution
    if video_width <= 640 and video_height <= 480:
        return 640, 480
    elif video_width <= 1280 and video_height <= 720:
        return 1280, 720
    elif video_width <= 1920 and video_height <= 1080:
        return 1920, 1080
    else:
        return 3840, 2160


def QUEUE(name, max_size_buffers=3, max_size_bytes=0, max_size_time=0, leaky="no"):
    """
    Creates a GStreamer queue element string with the specified parameters.

    Args:
        name (str): The name of the queue element.
        max_size_buffers (int, optional): The maximum number of buffers that the queue can hold. Defaults to 3.
        max_size_bytes (int, optional): The maximum size in bytes that the queue can hold. Defaults to 0 (unlimited).
        max_size_time (int, optional): The maximum size in time that the queue can hold. Defaults to 0 (unlimited).
        leaky (str, optional): The leaky type of the queue. Can be 'no', 'upstream', or 'downstream'. Defaults to 'no'.

    Returns:
        str: A string representing the GStreamer queue element with the specified parameters.
    """
    q_string = f"queue name={name} leaky={leaky} max-size-buffers={max_size_buffers} max-size-bytes={max_size_bytes} max-size-time={max_size_time} "
    return q_string


def SOURCE_PIPELINE(
    video_source,
    video_width=640,
    video_height=640,
    video_format="RGB",
    name="source",
    no_webcam_compression=False,
    auth_username=None,
    auth_password=None,
):
    """
    Creates a GStreamer pipeline string for the video source.

    Args:
        video_source (str): The path or device name of the video source.
        video_width (int, optional): The width of the video. Defaults to 640.
        video_height (int, optional): The height of the video. Defaults to 640.
        video_format (str, optional): The video format. Defaults to 'RGB'.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'source'.
        auth_username (str, optional): Username for authentication (IP cameras).
        auth_password (str, optional): Password for authentication (IP cameras).

    Returns:
        str: A string representing the GStreamer pipeline for the video source.
    """
    source_type = get_source_type(video_source)

    if source_type == "usb":
        if no_webcam_compression:
            # When using uncomressed format, only low resolution is supported
            source_element = (
                f"v4l2src device={video_source} name={name} ! "
                f"video/x-raw, format=RGB, width=640, height=480 ! "
                "videoflip name=videoflip video-direction=horiz ! "
            )
        else:
            # Use compressed format for webcam
            width, height = get_camera_resulotion(video_width, video_height)
            source_element = (
                f"v4l2src device={video_source} name={name} ! image/jpeg, framerate=30/1, width={width}, height={height} ! "
                f"{QUEUE(name=f'{name}_queue_decoder', leaky='downstream', max_size_buffer=3)} ! "
                f"decodebin name={name}_decodebin ! "
                f"videoflip name=videoflip video-direction=horiz ! "
            )
    elif source_type == "rpi":
        source_element = (
            "appsrc name=app_source is-live=true leaky-type=downstream max-buffers=3 ! "
            "videoflip name=videoflip video-direction=horiz ! "
            # f'video/x-raw, format={video_format}, width={video_width}, height={video_height} ! '
        )
    elif source_type == "libcamera":
        source_element = (
            f"libcamerasrc name={name} ! "
            f"video/x-raw, format={video_format}, width=1536, height=864 ! "
        )
    elif source_type == "ximage":
        source_element = (
            f"ximagesrc xid={video_source} ! "
            f"{QUEUE(name=f'{name}queue_scale_')} ! "
            f"videoscale ! "
        )
    elif source_type == "rtsp":
        # RTSP source for IP cameras
        # Add authentication to URL if provided
        if auth_username and auth_password:
            # Parse URL and add authentication
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(video_source)
            netloc_with_auth = f"{auth_username}:{auth_password}@{parsed.netloc}"
            auth_url = urlunparse((parsed.scheme, netloc_with_auth, parsed.path, 
                                   parsed.params, parsed.query, parsed.fragment))
            rtsp_location = auth_url
        else:
            rtsp_location = video_source
            
        # source_element = (
        #     f"rtspsrc name={name} location=\"{rtsp_location}\" "
        #     f"latency=200 buffer-mode=auto drop-on-latency=true "
        #     f"protocols=tcp timeout=5000000 tcp-timeout=5000000 "
        #     f"retry=5 do-retransmission=true ! "
        #     f"{QUEUE(name=f'{name}_rtsp_queue', leaky='downstream', max_size_buffers=5)} ! "
        #     f"rtph264depay ! h264parse ! "
        #     f"{QUEUE(name=f'{name}_queue_decoder', leaky='downstream', max_size_buffers=3)} ! "
        #     f"decodebin name={name}_decodebin ! "
        # )

        source_element = (
            f"rtspsrc name={name} location=\"{rtsp_location}\" "
            f"latency=200 "
            f"protocols=tcp !"
            f"rtph264depay ! h264parse ! "
            f"decodebin name={name}_decodebin ! "
        )

    elif source_type == "http":
        # HTTP source for IP cameras (MJPEG streams)
        # Add authentication if provided
        auth_str = ""
        if auth_username and auth_password:
            auth_str = f"user-id=\"{auth_username}\" user-pw=\"{auth_password}\" "
            
        source_element = (
            f"souphttpsrc name={name} location=\"{video_source}\" "
            f"{auth_str}is-live=true do-timestamp=true ! "
            f"{QUEUE(name=f'{name}_http_queue', leaky='downstream', max_size_buffers=10)} ! "
            f"multipartdemux ! "
            f"{QUEUE(name=f'{name}_demux_queue', leaky='downstream', max_size_buffers=3)} ! "
        )
    else:
        source_element = (
            f'filesrc location="{video_source}" name={name} ! '
            f"{QUEUE(name=f'{name}_queue_decode')} ! "
            f"decodebin name={name}_decodebin ! "
        )

    source_pipeline = (
        f"{source_element} "
        f"{QUEUE(name=f'{name}_scale_q')} ! "
        f"videoscale name={name}_videoscale n-threads=2 ! "
        f"{QUEUE(name=f'{name}_convert_q')} ! "
        f"videoconvert n-threads=3 name={name}_convert qos=false ! "
        f"video/x-raw, pixel-aspect-ratio=1/1, format={video_format}, width={video_width}, height={video_height} "
    )

    return source_pipeline


def INFERENCE_PIPELINE(
    hef_path,
    post_process_so=None,
    batch_size=1,
    config_json=None,
    post_function_name=None,
    additional_params="",
    name="inference",
    # Extra hailonet parameters
    scheduler_timeout_ms=None,
    scheduler_priority=None,
    vdevice_group_id=1,
    multi_process_service=None,
):
    """
    Creates a GStreamer pipeline string for inference and post-processing using a user-provided shared object file.
    This pipeline includes videoscale and videoconvert elements to convert the video frame to the required format.
    The format and resolution are automatically negotiated based on the HEF file requirements.

    Args:
        hef_path (str): Path to the HEF file.
        post_process_so (str or None): Path to the post-processing .so file. If None, post-processing is skipped.
        batch_size (int): Batch size for hailonet (default=1).
        config_json (str or None): Config JSON for post-processing (e.g., label mapping).
        post_function_name (str or None): Function name in the .so postprocess.
        additional_params (str): Additional parameters appended to hailonet.
        name (str): Prefix name for pipeline elements (default='inference').

        # Extra hailonet parameters
        Run `gst-inspect-1.0 hailonet` for more information.
        vdevice_group_id (int): hailonet vdevice-group-id. Default=1.
        scheduler_timeout_ms (int or None): hailonet scheduler-timeout-ms. Default=None.
        scheduler_priority (int or None): hailonet scheduler-priority. Default=None.
        multi_process_service (bool or None): hailonet multi-process-service. Default=None.

    Returns:
        str: A string representing the GStreamer pipeline for inference.
    """
    # config & function strings
    config_str = f" config-path={config_json} " if config_json else ""
    function_name_str = (
        f" function-name={post_function_name} " if post_function_name else ""
    )
    vdevice_group_id_str = f" vdevice-group-id={vdevice_group_id} "
    multi_process_service_str = (
        f" multi-process-service={str(multi_process_service).lower()} "
        if multi_process_service is not None
        else ""
    )
    scheduler_timeout_ms_str = (
        f" scheduler-timeout-ms={scheduler_timeout_ms} "
        if scheduler_timeout_ms is not None
        else ""
    )
    scheduler_priority_str = (
        f" scheduler-priority={scheduler_priority} "
        if scheduler_priority is not None
        else ""
    )
    # Get the directory for post-processing shared objects
    tappas_post_process_dir = os.environ.get("TAPPAS_POST_PROC_DIR", "")
    whole_buffer_crop_so = os.path.join(
        tappas_post_process_dir, "cropping_algorithms/libwhole_buffer.so"
    )

    hailonet_str = (
        f"hailonet name={name}_hailonet "
        f"hef-path={hef_path} "
        f"batch-size={batch_size} "
        f"{vdevice_group_id_str}"
        f"{multi_process_service_str}"
        f"{scheduler_timeout_ms_str}"
        f"{scheduler_priority_str}"
        f"{additional_params} "
        f"force-writable=true "
    )
    bypass_max_size_buffers = 20

    inference_pipeline = (
        f"{QUEUE(name=f'{name}_input_q')} ! "
        f"hailocropper name={name}_crop so-path={whole_buffer_crop_so} function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true "
        f"hailoaggregator name={name}_agg "
        f"{name}_crop. ! {QUEUE(max_size_buffers=bypass_max_size_buffers, name=f'{name}_bypass_q')} ! {name}_agg.sink_0 "
        f"{name}_crop. ! "
        f"{QUEUE(name=f'{name}_scale_q')} ! "
        f"videoscale name={name}_videoscale n-threads=2 qos=false ! "
        f"{QUEUE(name=f'{name}_convert_q')} ! "
        f"video/x-raw, pixel-aspect-ratio=1/1 ! "
        f"videoconvert name={name}_videoconvert n-threads=2 ! "
        f"{QUEUE(name=f'{name}_hailonet_q')} ! "
        f"{hailonet_str} ! "
    )

    if post_process_so:
        inference_pipeline += (
            f"{QUEUE(name=f'{name}_hailofilter_q')} ! "
            f"hailofilter name={name}_hailofilter so-path={post_process_so} {config_str} {function_name_str} qos=false ! "
        )

    inference_pipeline += (
        f"{name}_agg.sink_1 {name}_agg. ! {QUEUE(name=f'{name}_output_q')}"
    )
    return inference_pipeline


def ATTRIBUTE_CLASSIFICATION_PIPELINE(
    postproc_module, hef_path, batch_size, name="classifier"
):
    tappas_post_process_dir = os.environ.get("TAPPAS_POST_PROC_DIR", "")
    cropper_so_path = os.path.join(
        tappas_post_process_dir, "cropping_algorithms/libmspn.so"
    )

    attribute_pipeline = (
        f"{QUEUE(name=f'{name}_detection_frames')} ! "
        f"hailocropper name={name}_cropper so-path={cropper_so_path} function-name=create_crops_only_person "
        f"hailoaggregator name={name}_agg "
        f"{name}_cropper. ! {QUEUE(name=f'{name}_full_frames')} ! {name}_agg. "
        f"{name}_cropper. ! hailonet hef-path={hef_path} batch-size={batch_size} scheduling-algorithm=1 scheduler-threshold=8 scheduler-timeout-ms=50 vdevice-group-id=1 ! hailopython module={postproc_module} ! {name}_agg. "
        f"{name}_agg. ! {QUEUE(name=f'{name}_output_q')} "
    )
    return attribute_pipeline


def INFERENCE_PIPELINE_WRAPPER(
    inner_pipeline, bypass_max_size_buffers=20, name="inference_wrapper"
):
    """
    Creates a GStreamer pipeline string that wraps an inner pipeline with a hailocropper and hailoaggregator.
    This allows to keep the original video resolution and color-space (format) of the input frame.
    The inner pipeline should be able to do the required conversions and rescale the detection to the original frame size.

    Args:
        inner_pipeline (str): The inner pipeline string to be wrapped.
        bypass_max_size_buffers (int, optional): The maximum number of buffers for the bypass queue. Defaults to 20.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'inference_wrapper'.

    Returns:
        str: A string representing the GStreamer pipeline for the inference wrapper.
    """
    # Get the directory for post-processing shared objects
    tappas_post_process_dir = os.environ.get("TAPPAS_POST_PROC_DIR", "")
    whole_buffer_crop_so = os.path.join(
        tappas_post_process_dir, "cropping_algorithms/libwhole_buffer.so"
    )

    # Construct the inference wrapper pipeline string
    inference_wrapper_pipeline = (
        f"{QUEUE(name=f'{name}_input_q')} ! "
        f"hailocropper name={name}_crop so-path={whole_buffer_crop_so} function-name=create_crops use-letterbox=true resize-method=inter-area internal-offset=true "
        f"hailoaggregator name={name}_agg "
        f"{name}_crop. ! {QUEUE(max_size_buffers=bypass_max_size_buffers, name=f'{name}_bypass_q')} ! {name}_agg.sink_0 "
        f"{name}_crop. ! {inner_pipeline} ! {name}_agg.sink_1 "
        f"{name}_agg. ! {QUEUE(name=f'{name}_output_q')} "
    )

    return inference_wrapper_pipeline


def OVERLAY_PIPELINE(name="hailo_overlay"):
    """
    Creates a GStreamer pipeline string for the hailooverlay element.
    This pipeline is used to draw bounding boxes and labels on the video.

    Args:
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_overlay'.

    Returns:
        str: A string representing the GStreamer pipeline for the hailooverlay element.
    """
    # Construct the overlay pipeline string
    overlay_pipeline = f"{QUEUE(name=f'{name}_q')} ! hailooverlay name={name} "

    return overlay_pipeline


def FILE_SINK_PIPELINE(
    output_file="resources/data/output.mp4", name="file_sink", bitrate=5000
):
    """
    Creates a GStreamer pipeline string for saving the video to a file in .mp4 format.
    It it recommended run ffmpeg to fix the file header after recording.
    example: ffmpeg -i output.mp4 -c copy fixed_output.mp4
    Note: If your source is a file, looping will not work with this pipeline.
    Args:
        output_file (str): The path to the output file.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'file_sink'.
        bitrate (int, optional): The bitrate for the encoder. Defaults to 5000.

    Returns:
        str: A string representing the GStreamer pipeline for saving the video to a file.
    """
    # Construct the file sink pipeline string
    file_sink_pipeline = (
        f"{QUEUE(name=f'{name}_videoconvert_q')} ! "
        f"videoconvert name={name}_videoconvert n-threads=2 qos=false ! "
        f"{QUEUE(name=f'{name}_encoder_q')} ! "
        f"x264enc tune=zerolatency bitrate={bitrate} ! "
        f"matroskamux ! "
        f"filesink location={output_file} "
    )

    return file_sink_pipeline


def NULL_SINK_PIPELINE(name="null_sink"):
    """
    Creates a GStreamer pipeline string for the null sink element.
    """
    return "fakesink sync=false "


def USER_CALLBACK_PIPELINE(name="identity_callback"):
    """
    Creates a GStreamer pipeline string for the user callback element.

    Args:
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'identity_callback'.

    Returns:
        str: A string representing the GStreamer pipeline for the user callback element.
    """
    # Construct the user callback pipeline string
    user_callback_pipeline = f"{QUEUE(name=f'{name}_q')} ! identity name={name} "

    return user_callback_pipeline


def TRACKER_PIPELINE(
    class_id,
    kalman_dist_thr=0.8,
    iou_thr=0.9,
    init_iou_thr=0.7,
    keep_new_frames=2,
    keep_tracked_frames=15,
    keep_lost_frames=2,
    keep_past_metadata=False,
    qos=False,
    name="hailo_tracker",
):
    """
    Creates a GStreamer pipeline string for the HailoTracker element.
    Args:
        class_id (int): The class ID to track. Default is -1, which tracks across all classes.
        kalman_dist_thr (float, optional): Threshold used in Kalman filter to compare Mahalanobis cost matrix. Closer to 1.0 is looser. Defaults to 0.8.
        iou_thr (float, optional): Threshold used in Kalman filter to compare IOU cost matrix. Closer to 1.0 is looser. Defaults to 0.9.
        init_iou_thr (float, optional): Threshold used in Kalman filter to compare IOU cost matrix of newly found instances. Closer to 1.0 is looser. Defaults to 0.7.
        keep_new_frames (int, optional): Number of frames to keep without a successful match before a 'new' instance is removed from the tracking record. Defaults to 2.
        keep_tracked_frames (int, optional): Number of frames to keep without a successful match before a 'tracked' instance is considered 'lost'. Defaults to 15.
        keep_lost_frames (int, optional): Number of frames to keep without a successful match before a 'lost' instance is removed from the tracking record. Defaults to 2.
        keep_past_metadata (bool, optional): Whether to keep past metadata on tracked objects. Defaults to False.
        qos (bool, optional): Whether to enable QoS. Defaults to False.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_tracker'.
    Note:
        For a full list of options and their descriptions, run `gst-inspect-1.0 hailotracker`.
    Returns:
        str: A string representing the GStreamer pipeline for the HailoTracker element.
    """
    # Construct the tracker pipeline string
    tracker_pipeline = (
        f"hailotracker name={name} class-id={class_id} kalman-dist-thr={kalman_dist_thr} iou-thr={iou_thr} init-iou-thr={init_iou_thr} "
        f"keep-new-frames={keep_new_frames} keep-tracked-frames={keep_tracked_frames} keep-lost-frames={keep_lost_frames} keep-past-metadata={keep_past_metadata} qos={qos} ! "
        f"{QUEUE(name=f'{name}_q')} "
    )
    return tracker_pipeline


def HAILOOSD_PIPELINE(name="hailoosd"):
    """
    Creates a GStreamer pipeline segment using HailoOSD for on-screen display.
    HailoOSD is designed specifically for Hailo platforms to display information
    like FPS counters, bounding boxes, and other annotations.

    Args:
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailoosd'.

    Returns:
        str: A string representing the GStreamer pipeline for HailoOSD.
    """
    # Construct the HailoOSD pipeline string
    hailoosd_pipeline = (
        f"{QUEUE(name=f'{name}_q')} ! "
        f"hailoosd name={name}_osd qos=false "
        f"show-fps=true "  # Enable FPS counter
        f"font-size=14 "  # Set font size
        f"text-color=0,1,0,1 "  # Green text (RGBA format: 0-1 range)
        f"font-family=Sans "  # Font family
        f"text-pos=top-right "  # Position of the text
        f"font-style=bold ! "  # Font style
    )

    return hailoosd_pipeline


def DISPLAY_PIPELINE(
    video_sink="autovideosink", sync="true", show_fps="false", name="hailo_display"
):
    """
    Creates a GStreamer pipeline string for displaying the video.
    It includes the hailooverlay plugin to draw bounding boxes and labels on the video.

    Args:
        video_sink (str, optional): The video sink element to use. Defaults to 'autovideosink'.
        sync (str, optional): The sync property for the video sink. Defaults to 'true'.
        show_fps (str, optional): Whether to show the FPS on the video sink. Should be 'true' or 'false'. Defaults to 'false'.
        name (str, optional): The prefix name for the pipeline elements. Defaults to 'hailo_display'.

    Returns:
        str: A string representing the GStreamer pipeline for displaying the video.
    """
    # Construct the display pipeline string
    display_pipeline = (
        # f'{OVERLAY_PIPELINE(name=f"{name}_overlay")} ! '
        # f'{QUEUE(name=f"{name}_videoconvert_q")} ! '
        f"videoconvert name={name}_videoconvert n-threads=2 qos=false ! "
        f"{QUEUE(name=f'{name}_q')} ! "
        f"fpsdisplaysink name={name} video-sink={video_sink} sync={sync} text-overlay={show_fps} signal-fps-measurements=true "
    )

    return display_pipeline


def BYTETRACK_PIPELINE() -> str:
    return f"{QUEUE('queue_tracking_callback')} ! identity name=tracking_callback "
