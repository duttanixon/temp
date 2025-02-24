from typing import Dict, Any
from core.interfaces.cloud.formatters.formatter import IMetricsFormatter
from core.implementation.cloud.formatters.flow_eye import FlowEyeMetricsFormatter

class MetricsFormatterFactory:
    """Factory for creating metrics formatters"""

    @staticmethod
    def create(config: Dict[str, Any]) -> IMetricsFormatter:
        """
        Creates a metrics formatter based on solution type.
        
        Args:
            config: Dictionary containing solution configuration
            
        Returns:
            BaseMetricsFormatter: Configured metrics formatter instance
            
        Raises:
            ValueError: If solution type is not supported
        """
        solution_type = config.get("solution_type", "").lower()
        report_interval = config.get("report_interval", None)
        
        # Registry of available formatters
        formatters = {
            "flow_eye": FlowEyeMetricsFormatter,
            # "behave_eye": BehaveEyeMetricsFormatter,
            # Add other solutions here as needed
        }
        
        formatter_class = formatters.get(solution_type)
        if not formatter_class:
            raise ValueError(f"Unsupported solution type: {solution_type}")
        
        # Create formatter with optional custom interval
        if report_interval:
            return formatter_class(report_interval=report_interval)
        return formatter_class()