from .pipeline_helper import(
    QUEUE,
    SOURCE_PIPELINE,
    FILE_SINK_PIPELINE,
    DISPLAY_PIPELINE,
    NULL_SINK_PIPELINE
)

def build_flow_eye_pipeline_string(pipe):
    """Build flow eye pipeline"""

    sink_key = getattr(pipe, 'sink_type', 'file')
    sink_factories = {
        'fake': lambda: NULL_SINK_PIPELINE(name='null_sink'),
        'display': lambda: DISPLAY_PIPELINE(name='display_sink'),
        'file': lambda: FILE_SINK_PIPELINE(
            output_file='resources/data/output.mkv',
            name='file_sink',
            bitrate=100
        )
    }
    sink_factory = sink_factories.get(sink_key, sink_factories['file'])
    sink_segment = sink_factory()

    source_segment = SOURCE_PIPELINE(pipe.video_source, pipe.video_width, pipe.video_height, video_format='RGB')

    fps_display_segment = (
        f"{QUEUE(name='fps_measure_queue')} ! "
        "identity name=fps_measure signal-handoffs=true "    # This element will be used to measure FPS
        "! videoconvert ! "                                  # Convert to format compatible with textoverlay
        "textoverlay text=\"FPS: 0.0\" "                     # Default text - will be updated by callback
        "valignment=top halignment=left "                    # Position at top-right
        "font-desc=\"Sans, 18\" "                            # Font size and family
        "name=fps_overlay ! "                                # Name for reference in callbacks
        f"{QUEUE(name='fps_overlay_queue')}"                 # Queue after text overlay
    )
    


    pipeline_string = (
        f"{source_segment} ! "
        + (f"{fps_display_segment} ! " if pipe.measure_fps else "")
        + f"{sink_segment}"
    )
    return pipeline_string
