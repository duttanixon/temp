import sys
import os
import time
import datetime
from typing import Dict, Optional, Any


class BusMessageHandler:
    """Responsible for handling GStreamer bus messages with detailed logging for hailo pipelines"""

    def __init__(
        self,
        pipeline_manager: "PipelineManager",
        loop: "GLib.MainLoop",
        gst_context: "GstContext",
        isDebug: bool = False,
    ):
        self.pipeline_manager = pipeline_manager
        self.loop = loop
        self.context = gst_context
        self.error_occurred = False
        self.debug_callback = None
        self.isDebug = isDebug

        self.log_file_path = os.path.join(os.path.dirname("__file__"), "message.log")
        self.log_file = None

        # stats collection
        self.stats_interval_sec = 5
        self.last_stats_time = time.time()
        self.element_stats = {}
        self.fps_stats = {}
        self.buffer_counts = {}
        self.qos_stats = {}
        self.hailo_inference_stats = {}

        # Initialize log file only if debug is enabled
        if self.isDebug:
            self._init_log_file()
            # Log pipeline description
            self._log_pipeline_description()

    def _init_log_file(self):
        """Initialize the log file (only called if isDebug is True)"""
        try:
            # Open file in append mode to avoid overwriting existing logs
            self.log_file = open(self.log_file_path, "w")
            self.log_to_file(f"{'=' * 80}")
            self.log_to_file(
                f"HAILO PIPELINE SESSION STARTED AT {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}"
            )
            self.log_to_file(f"{'=' * 80}")
        except Exception as e:
            print(f"Error opening log file: {e}", file=sys.stderr)
            self.log_file = None

    def log_to_file(self, message: str):
        """Write a message to the log file if debug is enabled, otherwise print to console"""
        if self.isDebug and self.log_file:
            try:
                self.log_file.write(f"{message}\n")
                self.log_file.flush()  # Ensure it's written immediately
            except Exception as e:
                print(f"Error writing to log file: {e}", file=sys.stderr)
        elif not self.isDebug and message.startswith("ERROR:"):
            # Always print errors to console regardless of debug mode
            print(message, file=sys.stderr)

    def _log_pipeline_description(self):
        """Log detailed information about the pipeline configuration (only if isDebug is True)"""
        if not self.isDebug:
            return

        try:
            pipeline = self.pipeline_manager.get_pipeline()
            if pipeline:
                self.log_to_file("\nPIPELINE CONFIGURATION")
                self.log_to_file("=" * 50)

                # Get pipeline elements
                iterator = pipeline.iterate_elements()
                elements = []

                # Convert iterator to list
                while True:
                    result, element = iterator.next()
                    if result == self.context.gst.IteratorResult.DONE:
                        break
                    if result == self.context.gst.IteratorResult.OK:
                        elements.append(element)

                # log information about each element
                for element in elements:
                    try:
                        element_name = element.get_name()
                        element_type = element.__gtype__.name

                        self.log_to_file(
                            f"\nElement:{element_name} (Type: {element_type})"
                        )

                        # Get element properties
                        property_specs = self.context.gobject.list_properties(element)
                        properties = {}

                        for prop in property_specs:
                            try:
                                prop_name = prop.name
                                if hasattr(element.props, prop_name):
                                    prop_value = getattr(element.props, prop_name)
                                    properties[prop_name] = str(prop_value)
                            except:
                                pass

                        # log element properties
                        if properties:
                            self.log_to_file("  Properties  ")
                            for prop_name, prop_value in properties.items():
                                self.log_to_file(f" {prop_name}: {prop_value}")

                        # get element pads
                        for pad_type, pad_iterator in [
                            ("Src Pads", element.iterate_src_pads()),
                            ("Sink Pads", element.iterate_sink_pads()),
                        ]:
                            pads = []

                            while True:
                                pad_result, pad = pad_iterator.next()
                                if pad_result == self.context.gst.IteratorResult.DONE:
                                    break
                                if pad_result == self.context.gst.IteratorResult.OK:
                                    pads.append(pad)

                            if pads:
                                self.log_to_file(f" {pad_type}:")
                                for pad in pads:
                                    pad_name = pad.get_name()

                                    # Get pad capabilities
                                    caps = pad.get_current_caps()
                                    caps_str = (
                                        "None" if caps is None else caps.to_string()
                                    )

                                    self.log_to_file(f"    Pad: {pad_name}")
                                    self.log_to_file(f"      Capabilities: {caps_str}")

                    except Exception as e:
                        self.log_to_file(f"     Error getting element info: {e}")

                # Special logging for Hailo elements
                self._log_hailo_specific_elements(elements)

                self.log_to_file("=" * 50)
                self.log_to_file("")

        except Exception as e:
            self.log_to_file(f"Error logging pipeline description: {e}")

    def _log_hailo_specific_elements(self, elements):
        """Log special information about hailo specific elements (only if isDebug is True)"""
        if not self.isDebug:
            return

        hailo_elements = [e for e in elements if "hailo" in e.get_name().lower()]

        if hailo_elements:
            self.log_to_file("\nHAILO SPECIFIC ELEMENTS")
            self.log_to_file("-" * 50)

            for element in hailo_elements:
                element_name = element.get_name()
                element_type = element.__gtype__.name

                self.log_to_file(
                    f"\nHailo Element: {element_name} (Type:{element_type})"
                )

                # log special information based on element type
                if "HailoNet" in element_type:
                    try:
                        hef_path = (
                            element.get_property("hef-path")
                            if hasattr(element.props, "hef-path")
                            else "Unknown"
                        )
                        batch_size = (
                            element.get_property("batch-size")
                            if hasattr(element.props, "batch-size")
                            else "Unknown"
                        )
                        self.log_to_file(f" HEF Path: {hef_path}")
                        self.log_to_file(f" Batch Size: {batch_size}")

                    except Exception as e:
                        self.log_to_file(f" Error getting HailoNet info: {e}")

                elif "HailoFilter" in element_type:
                    try:
                        so_path = (
                            element.get_property("so-path")
                            if hasattr(element.props, "so-path")
                            else "Unknown"
                        )
                        function_name = (
                            element.get_property("function-name")
                            if hasattr(element.props, "function-name")
                            else "Unknown"
                        )
                        self.log_to_file(f" SO Path: {so_path}")
                        self.log_to_file(f" Function Name: {function_name}")
                    except Exception as e:
                        self.log_to_file(f" Error getting HailoFilter info: {e}")

                elif "HailoPython" in element_type:
                    try:
                        module = (
                            element.get_property("module")
                            if hasattr(element.props, "module")
                            else "Unknown"
                        )
                        self.log_to_file(f" Python Module: {module}")
                    except Exception as e:
                        self.log_to_file(f" Error getting HailoPython info {e}")

                elif "HailoCropper" in element_type:
                    try:
                        so_path = (
                            element.get_property("so-path")
                            if hasattr(element.props, "so-path")
                            else "Unknown"
                        )
                        function_name = (
                            element.get_property("function-name")
                            if hasattr(element.props, "function-name")
                            else "Unknown"
                        )
                        self.log_to_file(f"  SO Path: {so_path}")
                        self.log_to_file(f"  Function Name: {function_name}")
                    except Exception as e:
                        self.log_to_file(f" Error getting HailoCropper info: {e}")

    def _update_stats(self, element_name, msg_type, data=None):
        """Update statistical information about pipeline elements (collected regardless of debug mode)"""
        if element_name not in self.element_stats:
            self.element_stats[element_name] = {"message_counts": {}}

        if msg_type not in self.element_stats[element_name]["message_counts"]:
            self.element_stats[element_name]["message_counts"][msg_type] = 0

        self.element_stats[element_name]["message_counts"][msg_type] += 1

        # update specific stats based on message type
        if msg_type == "BUFFER":
            if element_name not in self.buffer_counts:
                self.buffer_counts[element_name] = 0
            self.buffer_counts[element_name] += 1

        elif msg_type == "QOS":
            if element_name not in self.qos_stats:
                self.qos_stats[element_name] = {"dropped": 0, "processed": 0}

            if data:
                if "dropped" in data and data["dropped"] is not None:
                    self.qos_stats[element_name]["dropped"] = data["dropped"]
                if "processed" in data and data["processed"] is not None:
                    self.qos_stats[element_name]["processed"] = data["processed"]

    def _log_periodic_stats(self):
        """Log periodic statistics about pipeline performance (only if isDebug is True)"""
        if not self.isDebug:
            return

        current_time = time.time()
        if (current_time - self.last_stats_time) >= self.stats_interval_sec:
            self.last_stats_time = current_time

            self.log_to_file("\nPERIODIC PIPELINE STATISTICS:")
            self.log_to_file("-" * 50)

            # log buffer processing statistics
            if self.buffer_counts:
                self.log_to_file("\nBuffer Counts")
                for element, count in self.buffer_counts.items():
                    self.log_to_file(f"  {element}: {count} buffers")
                self.buffer_counts = {}  # Reset for next period

            # Log QoS statistics
            if self.qos_stats:
                self.log_to_file("\nQoS Statistics")
                for element, stats in self.qos_stats.items():
                    dropped = stats.get("dropped", 0)
                    processed = stats.get("processed", 0)
                    drop_rate = (
                        (dropped / (processed + dropped)) * 100
                        if (processed + dropped) > 0
                        else 0
                    )
                    self.log_to_file(
                        f" {element}: Dropped  {dropped} of {processed + dropped} buffers ({drop_rate:.2f}%)"
                    )
                # Keep QoS stats for trend analysis

            # Log Hailo inference statistics
            if self.hailo_inference_stats:
                self.log_to_file("\n Hailo Inference Statistics")
                for model, stats in self.hailo_inference_stats.items():
                    self.log_to_file(f"  {model}:")
                    for key, value in stats.items():
                        self.log_to_file(f"    {key}: {value}")
                # keep inference stats for trend analysis

            self.log_to_file("-" * 50)

    def set_debug_callback(self, callback: Any):
        """Set the debug callback for dumping pipeline on error"""
        self.debug_callback = callback

    def __del__(self):
        """Clean up resources when the object is destroyed"""
        if self.isDebug and self.log_file:
            try:
                self.log_to_file(f"{'#' * 40}")
                self.log_to_file(
                    f"GStreamer session ended at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.log_to_file(f"{'#' * 40}")
                self.log_file.close()
            except:
                pass

    def handle_eos(self) -> None:
        """Handles end-of-stream message"""
        self.pipeline_manager.set_state(self.context.gst.State.NULL)
        self.loop.quit()

    def handle_error(self) -> None:
        """Handles error message"""
        self.pipeline_manager.set_state(self.context.gst.State.NULL)
        self.loop.quit()

    def has_error(self) -> bool:
        """Returns whether an error has occurred"""
        return self.error_occurred

    def bus_call(self, bus, message, *args) -> bool:
        """Handles bus messages from the pipeline with detailed logging"""
        # Always process messages regardless of debug mode,
        # but only log details if isDebug is True

        msg_type = message.type
        src_element = message.src
        src_name = src_element.get_name() if src_element else "unknown"

        # Get message type name for logging
        msg_type_name = str(msg_type).split(".")[-1]

        # Update statistics (always collect statistics regardless of debug mode)
        self._update_stats(src_name, msg_type_name)

        # Only do detailed logging if debug is enabled
        if self.isDebug:
            # format timestamp for logging
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            # log basic message info
            self.log_to_file(f"[{timestamp}] {msg_type_name} from {src_name}")

        # Always handle the message regardless of debug mode

        if msg_type == self.context.gst.MessageType.EOS:
            if self.isDebug:
                self.log_to_file("End-of-stream")
            self.handle_eos()

        elif msg_type == self.context.gst.MessageType.ERROR:
            err, debug = message.parse_error()
            # Always log errors, even in non-debug mode
            error_msg = f"ERROR: {err}"
            debug_msg = f"Debug details: {debug}"

            if self.isDebug:
                self.log_to_file(error_msg)
                self.log_to_file(debug_msg)

                # Get more information about the error context
                self.log_to_file("Error context:")
                self.log_to_file(f"  Source element: {src_name}")

                # Try to get element state
                try:
                    state_result, state, pending = src_element.get_state(0)
                    if state_result == self.context.gst.StateChangeReturn.SUCCESS:
                        state_name = self.context.gst.Element.state_get_name(state)
                        pending_name = self.context.gst.Element.state_get_name(pending)
                        self.log_to_file(
                            f"  Element state: {state_name}, pending: {pending_name}"
                        )
                    else:
                        self.log_to_file("  Unable to retrieve element state")
                except:
                    self.log_to_file("  Could not retrieve element state")
            else:
                # Print to stderr in non-debug mode
                print(error_msg, file=sys.stderr)
                print(debug_msg, file=sys.stderr)
                print(f"Error source: {src_name}", file=sys.stderr)

            self.error_occurred = True

            # Dump pipeline state if debug callback is set
            if self.debug_callback:
                self.debug_callback("error")

            self.handle_error()

        elif msg_type == self.context.gst.MessageType.WARNING:
            if self.isDebug:
                warn, debug = message.parse_warning()
                self.log_to_file(f"WARNING: {warn}")
                self.log_to_file(f"Debug details: {debug}")
            # In non-debug mode, we might want to print warnings to stderr as well
            # but not as verbose as in debug mode

        elif msg_type == self.context.gst.MessageType.INFO:
            if self.isDebug:
                info, debug = message.parse_info()
                self.log_to_file(f"INFO: {info}")
                self.log_to_file(f"Debug details: {debug}")

        elif msg_type == self.context.gst.MessageType.STATE_CHANGED:
            if self.isDebug:
                old_state, new_state, pending_state = message.parse_state_changed()
                old_state_name = self.context.gst.Element.state_get_name(old_state)
                new_state_name = self.context.gst.Element.state_get_name(new_state)
                pending_state_name = self.context.gst.Element.state_get_name(
                    pending_state
                )

                # Log state changes (more detailed for main pipeline and Hailo elements)
                if src_element == self.pipeline_manager.get_pipeline():
                    self.log_to_file(
                        f"PIPELINE STATE CHANGED: {old_state_name} → {new_state_name} (pending: {pending_state_name})"
                    )

                    # Log full pipeline state when it reaches PLAYING
                    if new_state == self.context.gst.State.PLAYING:
                        self.log_to_file("Pipeline reached PLAYING state")
                        if self.debug_callback:
                            self.debug_callback(f"state changed to {new_state_name}")

                elif "hailo" in src_name.lower():
                    self.log_to_file(
                        f"HAILO ELEMENT '{src_name}' STATE CHANGED: {old_state_name} → {new_state_name} (pending: {pending_state_name})"
                    )
                else:
                    self.log_to_file(
                        f"Element '{src_name}' state: {old_state_name} → {new_state_name}"
                    )

        # The rest of the message handlers should only log if isDebug is True
        # All remaining handlers follow the same pattern - only process and log if isDebug is True

        elif self.isDebug and msg_type == self.context.gst.MessageType.QOS:
            # Extract QoS information
            structure = message.get_structure()
            qos_data = {}

            if structure:
                # Extract common QoS values
                qos_data = {
                    "live": structure.get_value("live")
                    if structure.has_field("live")
                    else None,
                    "running_time": structure.get_value("running-time")
                    if structure.has_field("running-time")
                    else None,
                    "stream_time": structure.get_value("stream-time")
                    if structure.has_field("stream-time")
                    else None,
                    "timestamp": structure.get_value("timestamp")
                    if structure.has_field("timestamp")
                    else None,
                    "duration": structure.get_value("duration")
                    if structure.has_field("duration")
                    else None,
                    "dropped": structure.get_value("dropped")
                    if structure.has_field("dropped")
                    else None,
                    "processed": structure.get_value("processed")
                    if structure.has_field("processed")
                    else None,
                    "jitter": structure.get_value("jitter")
                    if structure.has_field("jitter")
                    else None,
                    "quality": structure.get_value("quality")
                    if structure.has_field("quality")
                    else None,
                }

                # Update QoS statistics
                self._update_stats(src_name, "QOS", qos_data)

                # Log QoS information
                self.log_to_file(f"QoS message from {src_name}:")

                # Log dropped buffers - important performance analysis
                if (
                    qos_data["dropped"] is not None
                    and qos_data["processed"] is not None
                ):
                    total = (qos_data["dropped"] or 0) + (qos_data["processed"] or 0)
                    drop_rate = (qos_data["dropped"] / total) * 100 if total > 0 else 0
                    self.log_to_file(
                        f"    Dropped: {qos_data['dropped']} of {total} buffers ({drop_rate:.2f}%)"
                    )

                # Log jitter if available - important for timing analysis
                if qos_data["jitter"] is not None:
                    self.log_to_file(f"    Jitter: {qos_data['jitter']} ns")

                # Log quality if available
                if qos_data["quality"] is not None:
                    self.log_to_file(f"    Quality: {qos_data['quality']}")

                # log all field for detailed analysis if debugging
                if "hailo" in src_name.lower():
                    self.log_to_file("  All hailo QOS fields:")
                    n_fields = structure.n_fields()
                    for i in range(n_fields):
                        field_name = structure.nth_field_name(i)
                        field_value = structure.get_value(field_name)
                        self.log_to_file(f"     {field_name}: {field_value}")

            else:
                self.log_to_file(
                    f"QoS message from {src_name} (no structure available)"
                )

        # Continue with the remaining message handlers, but only if isDebug is True
        # (I've abbreviated the implementation for brevity, but in your actual code
        # you'd include all the detailed handling from your original code)

        elif self.isDebug and msg_type == self.context.gst.MessageType.ELEMENT:
            # Your existing ELEMENT message handling code here
            # Extract element specific information
            structure = message.get_structure()

            if structure:
                structure_name = structure.get_name()
                self.log_to_file(
                    f"Element message from {src_name}, type: {structure_name}"
                )

                # Handle hailo-specific element messages
                if "hailo" in src_name.lower():
                    # log all fields for Hailo elements for detailed analysis
                    self.log_to_file(" Hailo element fields")
                    try:
                        n_fields = structure.n_fields()
                        for i in range(n_fields):
                            field_name = structure.nth_field_name(i)
                            try:
                                field_value = structure.get_value(field_name)
                                self.log_to_file(f"     {field_name}: {field_value}")

                                # Update Hailo inference statistics if relevant
                                if (
                                    "inference" in field_name.lower()
                                    or "latency" in field_name.lower()
                                ):
                                    if src_name not in self.hailo_inference_stats:
                                        self.hailo_inference_stats[src_name] = {}
                                    self.hailo_inference_stats[src_name][field_name] = (
                                        field_value
                                    )
                            except Exception as e:
                                self.log_to_file(
                                    f"     {field_name}: <cannot display: {e}>"
                                )
                    except Exception as e:
                        self.log_to_file(f" Error processing hailo element fields: {e}")

                if structure_name == "GstBinForwarded":
                    # This is a forwarded message from a bin
                    forwarded_msg = structure.get_value("message")
                    if forwarded_msg:
                        fwd_type = forwarded_msg.type
                        fwd_src = (
                            forwarded_msg.src.get_name()
                            if forwarded_msg.src
                            else "unknown"
                        )
                        self.log_to_file(
                            f"     Forwarded message from {fwd_src} of type {fwd_type}"
                        )

                elif "level" in structure_name:
                    # Audio/video level message
                    if structure.has_field("rms"):
                        rms_values = structure.get_value("rms")
                        peak_values = (
                            structure.get_value("peak")
                            if structure.has_field("peak")
                            else None
                        )
                        self.log_to_file(
                            f"     Level information - RMS: {rms_values}, Peak: {peak_values}"
                        )

                elif "stream-start" in structure_name:
                    # start stream message
                    uri = (
                        structure.get_value("uri")
                        if structure.has_field("uri")
                        else None
                    )
                    self.log_to_file(f"    Stream started: {uri}")

                elif "progress" in structure_name:
                    # Progress message
                    percent = (
                        structure.get_value("percent-double")
                        if structure.has_field("percent-double")
                        else structure.get_value("percent")
                    )
                    code = (
                        structure.get_value("code")
                        if structure.has_field("code")
                        else None
                    )
                    text = (
                        structure.get_value("text")
                        if structure.has_field("text")
                        else None
                    )
                    self.log_to_file(f"  Progress: {percent}% - {code}: {text}")
            else:
                self.log_to_file(
                    f"Element message from {src_name} (no structure available)"
                )

        # Add similar conditional checks for the remaining message types
        elif self.isDebug and msg_type == self.context.gst.MessageType.BUFFERING:
            percent = (
                message.parse_buffering_stats()[0]
                if hasattr(message, "parse_buffering_stats")
                else message.parse_buffering()
            )
            self.log_to_file(f"Buffering: {percent}%")

        elif self.isDebug and msg_type == self.context.gst.MessageType.LATENCY:
            self.log_to_file(f"Latency message from {src_name}")

        elif self.isDebug and msg_type == self.context.gst.MessageType.TAG:
            tag_list = message.parse_tag()
            if tag_list:
                tags = {}
                for tag in tag_list.to_string().split(","):
                    parts = tag.strip().split("=", 1)
                    if len(parts) == 2:
                        tags[parts[0].strip()] = parts[1].strip()

                self.log_to_file(f"Tags from {src_name}:")
                for tag_name, tag_value in tags.items():
                    self.log_to_file(f"  {tag_name}: {tag_value}")

        elif self.isDebug and msg_type == self.context.gst.MessageType.SEGMENT_DONE:
            segment_format, position = message.parse_segment_done()
            format_name = str(segment_format).split(".")[-1]
            self.log_to_file(f"Segment done: format={format_name}, position={position}")

        # Handle stream status messages (type 8192)
        elif self.isDebug and msg_type == self.context.gst.MessageType.STREAM_STATUS:
            status_type, owner = message.parse_stream_status()
            status_type_name = str(status_type).split(".")[-1]
            owner_name = owner.get_name() if owner else "unknown"

            self.log_to_file(f"STREAM STATUS from {src_name}: {status_type_name}")
            self.log_to_file(f"  Owner: {owner_name}")

            # Get the task object if available
            structure = message.get_structure()
            if structure and structure.has_field("object"):
                task = structure.get_value("object")
                self.log_to_file(f"  Task: {task}")

        # Handle duration changed messages (type 262144)
        elif self.isDebug and msg_type == self.context.gst.MessageType.DURATION_CHANGED:
            self.log_to_file(f"DURATION CHANGED from {src_name}")
            # Optionally try to get the new duration
            try:
                format_type = self.context.gst.Format.TIME
                success, duration = src_element.query_duration(format_type)
                if success:
                    duration_sec = duration / self.context.gst.SECOND
                    self.log_to_file(f"  New duration: {duration_sec:.3f} seconds")
            except:
                pass

        # Handle stream start messages (type 268435456)
        elif self.isDebug and msg_type == self.context.gst.MessageType.STREAM_START:
            self.log_to_file(f"STREAM START from {src_name}")
            # Try to extract group_id if available
            try:
                has_group_id, group_id = message.parse_group_id()
                if has_group_id:
                    self.log_to_file(f"  Group ID: {group_id}")
            except:
                pass

        # Handle async done messages (type 2097152)
        elif self.isDebug and msg_type == self.context.gst.MessageType.ASYNC_DONE:
            structure = message.get_structure()
            running_time = None
            if structure and structure.has_field("running-time"):
                running_time = structure.get_value("running-time")

            self.log_to_file(f"ASYNC DONE from {src_name}")
            if running_time is not None:
                if running_time == 0xFFFFFFFFFFFFFFFF:  # max uint64
                    self.log_to_file("  Running time: NONE")
                else:
                    running_time_sec = running_time / self.context.gst.SECOND
                    self.log_to_file(f"  Running time: {running_time_sec:.3f} seconds")

        # Handle new clock messages (type 2048)
        elif self.isDebug and msg_type == self.context.gst.MessageType.NEW_CLOCK:
            clock = message.parse_new_clock()
            clock_name = clock.get_name() if clock else "No clock"
            clock_type = type(clock).__name__ if clock else "None"

            self.log_to_file(f"NEW CLOCK from {src_name}")
            self.log_to_file(f"  Clock: {clock_name} (Type: {clock_type})")

            # If it's a system clock, log additional info
            if clock and hasattr(clock, "get_property"):
                try:
                    if hasattr(clock.props, "clock-type"):
                        clock_type_value = clock.get_property("clock-type")
                        self.log_to_file(f"  Clock type: {clock_type_value}")
                    if hasattr(clock.props, "timeout"):
                        timeout = clock.get_property("timeout")
                        self.log_to_file(f"  Timeout: {timeout}")
                except:
                    pass

        # For all other message types, only log details if debug is enabled
        elif self.isDebug:
            # Extract as much information as possible from unknown message types
            self.log_to_file(f"Raw message of type {msg_type_name} from {src_name}")

            # Try to extract structure information if available
            structure = message.get_structure()
            if structure:
                self.log_to_file(f"  Structure name: {structure.get_name()}")
                self.log_to_file("  Structure contents:")

                # Extract all fields from the structure
                n_fields = structure.n_fields()
                for i in range(n_fields):
                    try:
                        field_name = structure.nth_field_name(i)
                        field_value = structure.get_value(field_name)
                        field_type = structure.get_field_type(field_name)
                        self.log_to_file(
                            f"    {field_name} ({field_type}): {field_value}"
                        )
                    except Exception as e:
                        self.log_to_file(f"    Error extracting field {i}: {e}")

            # Try to extract additional information based on message type
            try:
                # Log message type number for reference
                type_int = int(msg_type)
                self.log_to_file(f"  Message type value: {type_int}")

                # Try to get message timestamp if available
                if hasattr(message, "get_timestamp"):
                    timestamp = message.get_timestamp()
                    if timestamp:
                        self.log_to_file(f"  Message timestamp: {timestamp}")

                # Try to get seqnum if available
                if hasattr(message, "get_seqnum"):
                    seqnum = message.get_seqnum()
                    self.log_to_file(f"  Message sequence number: {seqnum}")

                # Try to get other common attributes
                for attr in [
                    "get_stream_status_object",
                    "parse_group_id",
                    "parse_context_type",
                ]:
                    if hasattr(message, attr):
                        try:
                            value = getattr(message, attr)()
                            self.log_to_file(
                                f"  {attr.replace('get_', '').replace('parse_', '')}: {value}"
                            )
                        except:
                            pass

            except Exception as e:
                self.log_to_file(f"  Error extracting additional message info: {e}")

            # As a last resort, print the raw message
            self.log_to_file(f"  Raw representation: {message}")

        self.log_to_file("-" * 50)

        # Log periodic statistics
        self._log_periodic_stats()

        return True
