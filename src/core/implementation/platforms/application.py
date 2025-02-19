from typing import Dict, Any
import setproctitle
import sys

class VideoAnalyticsApp:
    """Video analytics application"""
    def __init__(self, config: Dict[str, Any], solution, platform):
        self.platform = platform
        self.config = config
        self.solution = solution
        self.initialize()


    def initialize(self) -> None:
        self.platform.initialize(self.config, self.solution)
        self.platform.setup_pipeline()

    def run(self) -> None:
        self.platform.run()
    



