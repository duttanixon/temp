# """
# Health monitoring module for the edge analytics application.
# Monitors system health, component status, and provides recovery mechanisms.
# """

# import os
# import time
# import threading
# import psutil
# import json
# from typing import Dict, Any, List, Optional, Callable
# from dataclasses import dataclass

# from core.implementation.common.logger import get_logger
# from core.implementation.common.error_handler import get_error_handler

# logger = get_logger()
# error_handler = get_error_handler()


# @dataclass
# class ComponentStatus:
#     """Status information for a system component"""
#     name: str
#     status: str  # "healthy", "degraded", "failed"
#     last_check: float
#     details: Dict[str, Any]
#     recovery_action: Optional[Callable] = None


# class HealthMonitor:
#     """
#     Monitors system health and component status.
#     Provides recovery mechanisms for unhealthy components.
#     """

#     # Singleton instance
#     _instance = None
#     _lock = threading.Lock()

#     @classmethod
#     def get_instance(cls) -> 'HealthMonitor':
#         """Get singleton instance of the health monitor"""
#         if cls._instance is None:
#             with cls._lock:
#                 if cls._instance is None:
#                     cls._instance = cls()
#         return cls._instance

#     def __init__(self):
#         """Initialize the health monitor"""
#         self.components: Dict[str, ComponentStatus] = {}
#         self.system_metrics: Dict[str, Any] = {}
#         self.running = False
#         self.monitor_thread = None
#         self.monitor_interval = 60  # seconds
#         self.health_file = "/var/log/edge-analytics/health.json"
#         self.metrics_file = "/var/log/edge-analytics/metrics.json"
        
#         # Create log directory if it doesn't exist
#         os.makedirs(os.path.dirname(self.health_file), exist_ok=True)

#     def register_component(
#         self, 
#         name: str, 
#         check_function: Callable[[], Dict[str, Any]],
#         recovery_action: Optional[Callable] = None
#     ) -> None:
#         """
#         Register a component for health monitoring.
        
#         Args:
#             name: Component name
#             check_function: Function to check component health, should return status dict
#             recovery_action: Optional function to call for recovery
#         """
#         component = ComponentStatus(
#             name=name,
#             status="unknown",
#             last_check=time.time(),
#             details={},
#             recovery_action=recovery_action
#         )
        
#         self.components[name] = component
        
#         # Register check function
#         setattr(self, f"_check_{name}", check_function)
        
#         logger.info(
#             f"Registered component for health monitoring: {name}",
#             component="HealthMonitor"
#         )

#     def start(self) -> None:
#         """Start the health monitoring thread"""
#         if self.running:
#             logger.info("Health monitor is already running", component="HealthMonitor")
#             return
            
#         self.running = True
#         self.monitor_thread = threading.Thread(target=self._monitor_loop)
#         self.monitor_thread.daemon = True
#         self.monitor_thread.start()
        
#         logger.info("Health monitor started", component="HealthMonitor")

#     def stop(self) -> None:
#         """Stop the health monitoring thread"""
#         self.running = False
#         if self.monitor_thread:
#             self.monitor_thread.join(timeout=5)
#         logger.info("Health monitor stopped", component="HealthMonitor")

#     def _monitor_loop(self) -> None:
#         """Main monitoring loop"""
#         while self.running:
#             try:
#                 # Check system health
#                 self._check_system_health()
                
#                 # Check each component
#                 for name in list(self.components.keys()):
#                     self._check_component(name)
                
#                 # Write health and metrics to files
#                 self._write_health_file()
#                 self._write_metrics_file()
                
#             except Exception as e:
#                 logger.error(
#                     "Error in health monitor loop",
#                     exception=e,
#                     component="HealthMonitor"
#                 )
                
#             # Sleep until next check
#             time.sleep(self.monitor_interval)

#     def _check_system_health(self) -> None:
#         """Check overall system health"""
#         # CPU usage
#         cpu_percent = psutil.cpu_percent(interval=1)
        
#         # Memory usage
#         memory = psutil.virtual_memory()
#         memory_percent = memory.percent
        
#         # Disk usage
#         disk = psutil.disk_usage('/')
#         disk_percent = disk.percent
        
#         # Temperature (if available)
#         temperature = {}
#         if hasattr(psutil, "sensors_temperatures"):
#             try:
#                 temps = psutil.sensors_temperatures()
#                 if temps:
#                     for name, entries in temps.items():
#                         for entry in entries:
#                             temperature[f"{name}_{entry.label or 'unknown'}"] = entry.current
#             except Exception:
#                 pass
                
#         # Network info
#         network = {}
#         net_io = psutil.net_io_counters()
#         network["bytes_sent"] = net_io.bytes_sent
#         network["bytes_recv"] = net_io.bytes_recv
#         network["packets_sent"] = net_io.packets_sent
#         network["packets_recv"] = net_io.packets_recv
#         network["errin"] = net_io.errin
#         network["errout"] = net_io.errout
        
#         # Process info
#         process = psutil.Process()
#         process_info = {
#             "cpu_percent": process.cpu_percent(interval=None),
#             "memory_percent": process.memory_percent(),
#             "num_threads": process.num_threads(),
#             "open_files": len(process.open_files())
#         }
        
#         # Update metrics
#         self.system_metrics = {
#             "timestamp": time.time(),
#             "cpu": {
#                 "percent": cpu_percent
#             },
#             "memory": {
#                 "total": memory.total,
#                 "available": memory.available,
#                 "used": memory.used,
#                 "percent": memory_percent
#             },
#             "disk": {
#                 "total": disk.total,
#                 "used": disk.used,
#                 "free": disk.free,
#                 "percent": disk_percent
#             },
#             "temperature": temperature,
#             "network": network,
#             "process": process_info
#         }
        
#         # Determine overall system health
#         system_status = "healthy"
#         if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
#             system_status = "degraded"
#             logger.warning(
#                 "System resources are near capacity",
#                 context={
#                     "cpu_percent": cpu_percent,
#                     "memory_percent": memory_percent,
#                     "disk_percent": disk_percent
#                 },
#                 component="HealthMonitor"
#             )
            
#         if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
#             system_status = "critical"
#             logger.error(
#                 "System resources are critically low",
#                 context={
#                     "cpu_percent": cpu_percent,
#                     "memory_percent": memory_percent,
#                     "disk_percent": disk_percent
#                 },
#                 component="HealthMonitor"
#             )
        
#         # Update system component status
#         self.components["system"] = ComponentStatus(
#             name="system",
#             status=system_status,
#             last_check=time.time(),
#             details=self.system_metrics,
#             recovery_action=self._recover_system if system_status == "critical" else None
#         )

#     def _check_component(self, name: str) -> None:
#         """
#         Check a specific component's health.
        
#         Args:
#             name: Component name
#         """
#         check_function = getattr(self, f"_check_{name}", None)
#         component = self.components.get(name)
        
#         if not check_function or not component:
#             return
            
#         try:
#             # Call the check function
#             details = check_function()
            
#             # Update component status
#             status = details.get("status", "unknown")
#             component.status = status
#             component.last_check = time.time()
#             component.details = details
            
#             # If component is not healthy, try recovery
#             if status != "healthy" and component.recovery_action:
#                 logger.warning(
#                     f"Component {name} is not healthy, attempting recovery",
#                     context={"status": status, "details": details},
#                     component="HealthMonitor"
#                 )
#                 try:
#                     component.recovery_action()
#                 except Exception as e:
#                     logger.error(
#                         f"Recovery action for {name} failed",
#                         exception=e,
#                         component="HealthMonitor"
#                     )
                    
#         except Exception as e:
#             logger.error(
#                 f"Error checking component {name}",
#                 exception=e,
#                 component="HealthMonitor"
#             )
#             component.status = "unknown"
#             component.last_check = time.time()
#             component.details = {"error": str(e)}

#     def _recover_system(self) -> None:
#         """Attempt to recover system resources"""
#         logger.info("Attempting to recover system resources", component="HealthMonitor")
        
#         try:
#             # Force garbage collection
#             import gc
#             gc.collect()
            
#             # Find and terminate memory-hogging processes (optional, use with caution)
#             if self.system_metrics.get("memory", {}).get("percent", 0) > 95:
#                 self._reduce_memory_usage()
                
#         except Exception as e:
#             logger.error(
#                 "Error during system recovery",
#                 exception=e,
#                 component="HealthMonitor"
#             )

#     def _reduce_memory_usage(self) -> None:
#         """Reduce memory usage by closing non-essential components"""
#         logger.warning(
#             "Attempting to reduce memory usage", 
#             component="HealthMonitor"
#         )
        
#         # This is application-specific and should be customized
#         # Example: close visualization, reduce buffer sizes, etc.
#         pass

#     def get_health_status(self) -> Dict[str, Any]:
#         """
#         Get the current health status of all components.
        
#         Returns:
#             Dict with health status of all components
#         """
#         status = {
#             "timestamp": time.time(),
#             "overall_status": self._get_overall_status(),
#             "components": {}
#         }
        
#         for name, component in self.components.items():
#             status["components"][name] = {
#                 "status": component.status,
#                 "last_check": component.last_check,
#                 "details": component.details
#             }
            
#         return status
        
#     def _get_overall_status(self) -> str:
#         """
#         Determine the overall system status based on component status.
        
#         Returns:
#             String with overall status ("healthy", "degraded", "critical")
#         """
#         if not self.components:
#             return "unknown"
            
#         statuses = [c.status for c in self.components.values()]
        
#         if "critical" in statuses:
#             return "critical"
#         elif "degraded" in statuses:
#             return "degraded"
#         elif all(s == "healthy" for s in statuses):
#             return "healthy"
#         else:
#             return "degraded"

#     def _write_health_file(self) -> None:
#         """Write health status to a file for external monitoring"""
#         try:
#             health_status = self.get_health_status()
#             with open(self.health_file, 'w') as f:
#                 json.dump(health_status, f, indent=2)
#         except Exception as e:
#             logger.error(
#                 "Error writing health file",
#                 exception=e,
#                 component="HealthMonitor"
#             )

#     def _write_metrics_file(self) -> None:
#         """Write system metrics to a file for external monitoring"""
#         try:
#             with open(self.metrics_file, 'w') as f:
#                 json.dump(self.system_metrics, f, indent=2)
#         except Exception as e:
#             logger.error(
#                 "Error writing metrics file",
#                 exception=e,
#                 component="HealthMonitor"
#             )


# # Default system component checks

# def check_pipeline() -> Dict[str, Any]:
#     """Check GStreamer pipeline health"""
#     # This is a placeholder - actual implementation would depend on 
#     # how we can get pipeline statistics
#     return {
#         "status": "healthy",
#         "details": {
#             "pipeline_state": "PLAYING",
#             "fps": 25.0,
#             "dropped_frames": 0
#         }
#     }


# def check_cloud_connection(cloud_connector) -> Dict[str, Any]:
#     """Check cloud connection health"""
#     if not cloud_connector:
#         return {
#             "status": "unknown",
#             "details": {
#                 "message": "Cloud connector not available"
#             }
#         }
        
#     try:
#         is_connected = cloud_connector.connection and cloud_connector.connection.is_connected()
        
#         return {
#             "status": "healthy" if is_connected else "degraded",
#             "details": {
#                 "connected": is_connected,
#                 "last_sync": getattr(cloud_connector, "last_sync_time", None),
#                 "pending_messages": cloud_connector.message_queue.qsize() if hasattr(cloud_connector, "message_queue") else 0
#             }
#         }
#     except Exception as e:
#         return {
#             "status": "degraded",
#             "details": {
#                 "error": str(e)
#             }
#         }


# # Global instance for easy import
# def get_health_monitor() -> HealthMonitor:
#     """Get the global health monitor instance"""
#     return HealthMonitor.get_instance()