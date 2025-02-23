"""
GStreamer Pipeline Debug Utilities
This module provides functions to visualize and debug GStreamer pipelines.
"""

import os
import subprocess
from typing import Optional, Dict, Any


class PipelineDebugger:
    """Provides methods to visualize and debug GStreamer pipelines"""

    def __init__(self, gst_context):
        """Initialize with GStreamer context"""
        self.context = gst_context

    def dump_dot_file(self, pipeline, filepath: str, state_name:str) -> str:
            """
            Dumps the pipeline structure to a dot file.
            
            Args:
                pipeline: The GStreamer pipeline to dump
                filename_prefix: Prefix for the output filename
                
            Returns:
                str: Path to the generated dot file or None if unsuccessful
            """
            # Dump the pipeline
            try:
                pipeline_name = pipeline.get_name()
                self.context.gst.debug_bin_to_dot_file(
                    pipeline, 
                    self.context.gst.DebugGraphDetails.ALL, 
                    f"{pipeline_name}_{state_name}"
                )
            except Exception as e:
                print("Failed to dump pipeline structure.....")
            
            # Construct the expected filename
            dot_file = os.path.join(
                filepath, 
                f"{pipeline_name}_{state_name}.dot"
            )
            
            # Check if the file was created
            if os.path.exists(dot_file):
                print(f"Pipeline structure dumped to: {dot_file}")
                return dot_file
            else:
                print("Failed to dump pipeline structure")
                return None


    def convert_dot_to_png(self, dot_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        Converts a dot file to PNG using the 'dot' tool from GraphViz.
        
        Args:
            dot_file: Path to the input dot file
            output_file: Path for the output PNG file (optional)
            
        Returns:
            str: Path to the generated PNG file or None if conversion failed
        """
        if not dot_file or not os.path.exists(dot_file):
            print(f"Dot file not found: {dot_file}")
            return None
            
        # If no output file specified, create one based on the input file
        if not output_file:
            output_file = os.path.splitext(dot_file)[0] + ".png"
            
        try:
            # Run dot command to convert
            subprocess.run(
                ["dot", "-Tpng", dot_file, "-o", output_file],
                check=True,
                capture_output=True
            )
            print(f"Converted to PNG: {output_file}")
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Error converting dot file: {e}")
            print(f"stdout: {e.stdout.decode()}")
            print(f"stderr: {e.stderr.decode()}")
            return None
        except FileNotFoundError:
            print("GraphViz 'dot' command not found. Make sure GraphViz is installed.")
            print("Install with: sudo apt-get install graphviz")
            return None

    def print_elements_tree(self, pipeline) -> None:
        """
        Prints a tree of elements in the pipeline to the console.
        
        Args:
            pipeline: The GStreamer pipeline
        """
        print("\nPipeline elements tree:")
        print("├── Pipeline:", pipeline.get_name())
        
        it = pipeline.iterate_elements()
        while True:
            result, element = it.next()
            if result != self.context.gst.IteratorResult.OK:
                break
                
            # Print element details
            print(f"│   ├── {element.get_name()} ({element.get_factory().get_name()})")
            
            # Print element properties
            for prop in self.context.gobject.list_properties(element):
                try:
                    value = element.get_property(prop.name)
                    if prop.name != "caps" and value is not None:
                        print(f"│   │   ├── {prop.name}: {value}")
                except:
                    # Some properties might not be readable
                    pass
                    
            # Print pads
            pad_iterator = element.iterate_pads()
            while True:
                pad_result, pad = pad_iterator.next()
                if pad_result != self.context.gst.IteratorResult.OK:
                    break
                    
                pad_name = pad.get_name()
                caps = pad.get_current_caps()
                caps_str = caps.to_string() if caps else "None"
                print(f"│   │   ├── Pad: {pad_name} ({caps_str})")


    def dump_pipeline(self, pipeline, filepath:str, state_name: str) -> Optional[str]:
        """
        Comprehensive pipeline dump - creates dot file, and prints stats.
        
        Args:
            pipeline: The GStreamer pipeline to dump
            base_filename: Base name for output files
            
        Returns:
            str: Path to the generated PNG file or None if unsuccessful
        """
        # Dump dot file
        dot_file = self.dump_dot_file(pipeline, filepath, state_name)
        if not dot_file:
            return None
        # Print element tree
        # self.print_elements_tree(pipeline)