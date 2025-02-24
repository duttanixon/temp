from datetime import datetime
from typing import Dict, Any, Optional
from core.interfaces.cloud.formatters.formatter import IMetricsFormatter

class FlowEyeMetricsFormatter(IMetricsFormatter):
    def __init__(self, report_interval: int=60):
        self.people_count = 0
        self.last_report_time = datetime.now()
        self.report_interval = report_interval # in seconds

    def format_metrics(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format FlowEye metrics - people count per minute"""
        current_time = datetime.now()
        
        # Update people count from detections
        detections = data.get("detections", [])
        self.people_count += len([d for d in detections if d.get("label") == "person"])
        
        # If interval has passed, prepare and reset metrics
        if (current_time - self.last_report_time).total_seconds() >= self.report_interval:
            metrics = {
                "type": "people_count",
                "interval": f"{self.report_interval}s",
                "count": self.people_count,
                "timestamp": current_time.isoformat()
            }
            self.people_count = 0
            self.last_report_time = current_time
            return metrics
            
        return None
