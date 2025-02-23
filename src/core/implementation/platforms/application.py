from typing import Dict, Any
import setproctitle
import sys
from core.interfaces.solutions.solution import ISolution
from core.interfaces.platforms.platform_controller import IPlatformController

class VideoAnalyticsApp:
    """Video analytics application"""
    def __init__(self, config: Dict[str, Any], solution: ISolution, platform:IPlatformController):
        self.platform = platform
        self.config = config
        self.solution = solution


    def initialize(self) -> None:
        self.platform.initialize()
        self.platform.setup_pipeline()

    def run(self) -> None:
        self.platform.run()
    



