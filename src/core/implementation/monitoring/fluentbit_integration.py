# """
# FluentBit integration module for the edge analytics application.
# Provides integration with FluentBit for log collection and forwarding.
# """

# import os
# import json
# import subprocess
# import time
# import shutil
# import threading
# import yaml
# from typing import Dict, Any, Optional, List

# from core.implementation.common.logger import get_logger
# from core.implementation.common.exceptions import SystemError

# logger = get_logger()


# class FluentBitManager:
#     """
#     Manages FluentBit integration for log collection and forwarding.
#     """

#     # Singleton instance
#     _instance = None
#     _lock = threading.Lock()

#     @classmethod
#     def get_instance(cls) -> 'FluentBitManager':
#         """Get singleton instance of the FluentBit manager"""
#         if cls._instance is None:
#             with cls._lock:
#                 if cls._instance is None:
#                     cls._instance = cls()
#         return cls._instance

#     def __init__(self):
#         """Initialize the FluentBit manager"""
#         self.config_dir = "/etc/edge-analytics/fluentbit"
#         self.log_dir = "/var/log/edge-analytics"
#         self.fluentbit_config_file = os.path.join(self.config_dir, "fluent-bit.conf")
#         self.fluentbit_process = None
#         self.is_running = False
#         self.monitor_thread = None
        
#         # Create config directory if it doesn't exist
#         os.makedirs(self.config_dir, exist_ok=True)
        
#         # Check if FluentBit is installed
#         self.is_installed = self._check_fluentbit_installed()

#     def _check_fluentbit_installed(self) -> bool:
#         """Check if FluentBit is installed"""
#         try:
#             result = subprocess.run(
#                 ["fluent-bit", "--version"], 
#                 stdout=subprocess.PIPE, 
#                 stderr=subprocess.PIPE
#             )
#             return result.returncode == 0
#         except FileNotFoundError:
#             logger.warning(
#                 "FluentBit not found. Log forwarding will be disabled.",
#                 component="FluentBitManager"
#             )
#             return False

#     def generate_config(
#         self, 
#         inputs: List[Dict[str, Any]], 
#         outputs: List[Dict[str, Any]],
#         cloud_config: Optional[Dict[str, Any]] = None
#     ) -> None:
#         """
#         Generate FluentBit configuration file.
        
#         Args:
#             inputs: List of input configurations
#             outputs: List of output configurations
#             cloud_config: Cloud-specific configuration
#         """
#         if not self.is_installed:
#             logger.warning(
#                 "Cannot generate FluentBit config: FluentBit not installed",
#                 component="FluentBitManager"
#             )
#             return
            
#         # Create config template
#         config = []
        
#         # Service section
#         config.append("[SERVICE]")
#         config.append("    Flush        5")
#         config.append("    Daemon       Off")
#         config.append("    Log_Level    info")
#         config.append("    HTTP_Server  On")
#         config.append("    HTTP_Listen  0.0.0.0")
#         config.append("    HTTP_Port    2020")
#         config.append("    Storage.path /var/log/edge-analytics/fluentbit-buffers")
#         config.append("    Storage.sync normal")
#         config.append("    Storage.checksum off")
#         config.append("    Storage.backlog.mem_limit 5M")
#         config.append("")
        
#         # Input sections
#         for i, input_config in enumerate(inputs):
#             input_type = input_config.get("type", "tail")
#             config.append(f"[INPUT]")
#             config.append(f"    Name         {input_type}")
            
#             if input_type == "tail":
#                 config.append(f"    Tag          edge-analytics.{input_config.get('tag', 'logs')}")
#                 config.append(f"    Path         {input_config.get('path', '/var/log/edge-analytics/edge-analytics-structured.json')}")
#                 config.append(f"    Parser       json")
#                 config.append(f"    DB           /var/log/edge-analytics/fluentbit-{i}.db")
                
#             elif input_type == "cpu":
#                 config.append(f"    Tag          edge-analytics.cpu")
#                 config.append(f"    Interval_Sec {input_config.get('interval', 60)}")
                
#             elif input_type == "mem":
#                 config.append(f"    Tag          edge-analytics.memory")
#                 config.append(f"    Interval_Sec {input_config.get('interval', 60)}")
                
#             # Add any other input-specific configuration
#             for key, value in input_config.items():
#                 if key not in ["type", "tag", "path", "interval"]:
#                     config.append(f"    {key}         {value}")
                    
#             config.append("")
        
#         # Parser section for JSON logs
#         config.append("[PARSER]")
#         config.append("    Name         json")
#         config.append("    Format       json")
#         config.append("    Time_Key     timestamp")
#         config.append("    Time_Format  %Y-%m-%dT%H:%M:%S.%L%z")
#         config.append("")
        
#         # Filter section to add device information
#         config.append("[FILTER]")
#         config.append("    Name         modify")
#         config.append("    Match        edge-analytics.*")
#         config.append(f"    Add          device_id {os.environ.get('DEVICE_ID', 'unknown')}")
#         config.append("")
        
#         # Output sections
#         for output_config in outputs:
#             output_type = output_config.get("type", "file")
#             config.append(f"[OUTPUT]")
#             config.append(f"    Name         {output_type}")
#             config.append(f"    Match        {output_config.get('match', 'edge-analytics.*')}")
            
#             if output_type == "file":
#                 config.append(f"    Path         {output_config.get('path', '/var/log/edge-analytics/processed')}")
                
#             elif output_type == "cloudwatch":
#                 if not cloud_config or cloud_config.get("provider") != "aws":
#                     logger.warning("CloudWatch output configured but AWS cloud config not provided")
#                     continue
                    
#                 config.append(f"    region       {cloud_config.get('region', 'us-east-1')}")
#                 config.append(f"    log_group_name {output_config.get('log_group', 'edge-analytics')}")
#                 config.append(f"    log_stream_prefix {output_config.get('log_stream_prefix', 'device-')}")
#                 config.append(f"    auto_create_group true")
                
#             elif output_type == "influxdb":
#                 config.append(f"    Host         {output_config.get('host', 'localhost')}")
#                 config.append(f"    Port         {output_config.get('port', 8086)}")
#                 config.append(f"    Database     {output_config.get('database', 'edge_analytics')}")
                
#             # Add any other output-specific configuration
#             for key, value in output_config.items():
#                 if key not in ["type", "match", "path", "host", "port", "database", "log_group", "log_stream_prefix"]:
#                     config.append(f"    {key}         {value}")
                    
#             config.append("")
        
#         # Write the config file
#         os.makedirs(os.path.dirname(self.fluentbit_config_file), exist_ok=True)
#         with open(self.fluentbit_config_file, "w") as f:
#             f.write("\n".join(config))
            
#         logger.info(
#             "Generated FluentBit configuration", 
#             context={"config_file": self.fluentbit_config_file},
#             component="FluentBitManager"
#         )

#     def start(self) -> bool:
#         """
#         Start the FluentBit process.
        
#         Returns:
#             bool: True if FluentBit was started successfully, False otherwise
#         """
#         if not self.is_installed:
#             logger.warning(
#                 "Cannot start FluentBit: FluentBit not installed",
#                 component="FluentBitManager"
#             )
#             return False
            
#         if self.is_running:
#             logger.info("FluentBit is already running", component="FluentBitManager")
#             return True
            
#         try:
#             # Create buffer directory
#             buffer_dir = "/var/log/edge-analytics/fluentbit-buffers"
#             os.makedirs(buffer_dir, exist_ok=True)
            
#             # Start FluentBit process
#             self.fluentbit_process = subprocess.Popen(
#                 ["fluent-bit", "-c", self.fluentbit_config_file],
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE
#             )
            
#             # Wait to see if it starts successfully
#             time.sleep(2)
            
#             if self.fluentbit_process.poll() is None:
#                 # Process is still running, start monitor thread
#                 self.is_running = True
#                 self.monitor_thread = threading.Thread(target=self._monitor_fluentbit)
#                 self.monitor_thread.daemon = True
#                 self.monitor_thread.start()
                
#                 logger.info("FluentBit started successfully", component="FluentBitManager")
#                 return True
#             else:
#                 # Process exited
#                 stdout, stderr = self.fluentbit_process.communicate()
#                 logger.error(
#                     "FluentBit failed to start",
#                     context={
#                         "stdout": stdout.decode() if stdout else "",
#                         "stderr": stderr.decode() if stderr else "",
#                         "exit_code": self.fluentbit_process.returncode
#                     },
#                     component="FluentBitManager"
#                 )
#                 self.fluentbit_process = None
#                 return False
                
#         except Exception as e:
#             logger.error(
#                 "Error starting FluentBit",
#                 exception=e,
#                 component="FluentBitManager"
#             )
#             return False

#     def stop(self) -> bool:
#         """
#         Stop the FluentBit process.
        
#         Returns:
#             bool: True if FluentBit was stopped successfully, False otherwise
#         """
#         if not self.is_running or not self.fluentbit_process:
#             logger.info("FluentBit is not running", component="FluentBitManager")
#             return True
            
#         try:
#             # Terminate the process
#             self.fluentbit_process.terminate()
            
#             # Wait for process to exit
#             try:
#                 self.fluentbit_process.wait(timeout=5)
#             except subprocess.TimeoutExpired:
#                 # Force kill if it doesn't exit
#                 self.fluentbit_process.kill()
#                 self.fluentbit_process.wait()
                
#             self.is_running = False
#             self.fluentbit_process = None
            
#             logger.info("FluentBit stopped successfully", component="FluentBitManager")
#             return True
            
#         except Exception as e:
#             logger.error(
#                 "Error stopping FluentBit",
#                 exception=e,
#                 component="FluentBitManager"
#             )
#             return False

#     def _monitor_fluentbit(self) -> None:
#         """Monitor the FluentBit process and restart if it fails"""
#         while self.is_running and self.fluentbit_process:
#             # Check if process is still running
#             if self.fluentbit_process.poll() is not None:
#                 # Process exited unexpectedly
#                 exit_code = self.fluentbit_process.returncode
#                 stdout, stderr = self.fluentbit_process.communicate()
                
#                 logger.error(
#                     "FluentBit process exited unexpectedly",
#                     context={
#                         "exit_code": exit_code,
#                         "stdout": stdout.decode() if stdout else "",
#                         "stderr": stderr.decode() if stderr else ""
#                     },
#                     component="FluentBitManager"
#                 )
                
#                 # Try to restart
#                 self.is_running = False
#                 time.sleep(5)  # Wait before restarting
#                 self.start()
#                 return  # Exit this thread, a new one will be started
                
#             # Sleep for a while before checking again
#             time.sleep(5)

#     def configure_from_cloud_config(self, cloud_config: Dict[str, Any]) -> None:
#         """
#         Configure FluentBit based on cloud configuration.
        
#         Args:
#             cloud_config: Cloud configuration dictionary
#         """
#         provider = cloud_config.get("provider", "").lower()
        
#         inputs = [
#             {
#                 "type": "tail",
#                 "tag": "logs",
#                 "path": "/var/log/edge-analytics/edge-analytics-structured.json"
#             },
#             {
#                 "type": "cpu",
#                 "interval": 60
#             },
#             {
#                 "type": "mem",
#                 "interval": 60
#             }
#         ]
        
#         outputs = []
        
#         # Add outputs based on provider
#         if provider == "aws_iot":
#             # CloudWatch Logs output
#             outputs.append({
#                 "type": "cloudwatch",
#                 "match": "edge-analytics.*",
#                 "log_group": "edge-analytics",
#                 "log_stream_prefix": f"device-{os.environ.get('DEVICE_ID', 'unknown')}-",
#                 "retry_limit": "5"
#             })
#         elif provider in ["azure_iot", "google_iot"]:
#             # For other providers, we can add appropriate outputs
#             # This is a placeholder for future implementation
#             pass
        
#         # Always add a file output as backup
#         outputs.append({
#             "type": "file",
#             "match": "edge-analytics.*",
#             "path": "/var/log/edge-analytics/processed"
#         })
        
#         # Generate the configuration
#         self.generate_config(inputs, outputs, cloud_config)
        
#         # Try to start FluentBit
#         self.start()


# # Global instance for easy import
# def get_fluentbit_manager() -> FluentBitManager:
#     """Get the global FluentBit manager instance"""
#     return FluentBitManager.get_instance()