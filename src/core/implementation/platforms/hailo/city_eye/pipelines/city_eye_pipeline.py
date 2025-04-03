import os
from .pipeline_helper import (
    QUEUE,
    SOURCE_PIPELINE,
    FILE_SINK_PIPELINE,
    DISPLAY_PIPELINE,
    NULL_SINK_PIPELINE,
    INFERENCE_PIPELINE,
    BYTETRACK_PIPELINE,
    OVERLAY_PIPELINE,
    USER_CALLBACK_PIPELINE,
    ATTRIBUTE_CLASSIFICATION_PIPELINE,
)


def build_city_eye_pipeline_string(pipe):
    """Build city eye pipeline"""

    sink_key = getattr(pipe, "sink_type", "file")
    sink_factories = {
        "fake": lambda: NULL_SINK_PIPELINE(name="null_sink"),
        "display": lambda: DISPLAY_PIPELINE(name="display_sink"),
        "file": lambda: FILE_SINK_PIPELINE(
            output_file="resources/data/output.mkv", name="file_sink", bitrate=1000
        ),
    }
    sink_factory = sink_factories.get(sink_key, sink_factories["file"])
    sink_segment = sink_factory()

    source_segment = SOURCE_PIPELINE(
        pipe.video_source, pipe.video_width, pipe.video_height, video_format="RGB"
    )

    detection_segment = INFERENCE_PIPELINE(
        hef_path=pipe.detection_model_path,
        post_process_so=pipe.post_process_so,
        post_function_name=pipe.post_function_name,
        batch_size=pipe.batch_size,
        config_json=pipe.labels_json,
        additional_params=pipe.thresholds_str,
    )

    tracking_segment = BYTETRACK_PIPELINE()

    person_attribute_post_process = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "hailopython",
        "attribute_prossprocess.py",
    )
    person_attribute_segment = ATTRIBUTE_CLASSIFICATION_PIPELINE(
        person_attribute_post_process,
        pipe.person_attributes_model_path,
        pipe.batch_size,
    )
    output_segment = USER_CALLBACK_PIPELINE(name="output_callback")
    overlay_segment = OVERLAY_PIPELINE()

    fps_display_segment = (
        f"{QUEUE(name='fps_measure_queue')} ! "
        "identity name=fps_measure signal-handoffs=true "  # This element will be used to measure FPS
        "! videoconvert ! "  # Convert to format compatible with textoverlay
        'textoverlay text="FPS: 0.0" '  # Default text - will be updated by callback
        "valignment=top halignment=left "  # Position at top-right
        'font-desc="Sans, 18" '  # Font size and family
        "name=fps_overlay ! "  # Name for reference in callbacks
        f"{QUEUE(name='fps_overlay_queue')}"  # Queue after text overlay
    )

    pipeline_string = (
        f"{source_segment} ! "
        + f"{detection_segment} ! "
        + f"{tracking_segment} ! "
        + f"{person_attribute_segment} ! "
        + f"{output_segment} ! "
        + (f"{fps_display_segment} ! " if pipe.measure_fps else "")
        + f"{overlay_segment} ! "
        + f"{sink_segment}"
    )
    return pipeline_string
