"""
Main entry point for the edge analytics application.
"""

from core.implementation.common.config_manager import ConfigManager
from core.implementation.platforms.application import VideoAnalyticsApp
from core.implementation.solutions.city_eye.solution import CityEyeSolution
from core.implementation.platforms.hailo.city_eye.controller import (
    HailoPipelineController,
)
from core.implementation.io.factories.input_factory import InputSourceFactory
from core.implementation.io.factories.output_factory import OutputHandlerFactory
from core.interfaces.solutions.solution import ISolution
from core.interfaces.platforms.platform_controller import IPlatformController
from core.interfaces.io.input_source import IInputSource
from core.interfaces.io.output_handler import IOutputHandler


def main():
    app = None 
    try:
        config_manager = ConfigManager("configs/city-eye.yaml")
        config = config_manager.load_config()

        # Create I/O handlers using factories
        input_source: IInputSource = InputSourceFactory.create(
            config["solution"]["input"]
        )
        
        output_handler: IOutputHandler = OutputHandlerFactory.create(
            config["solution"]["output"]
        )

        solution: ISolution = CityEyeSolution(
            config["solution"], input_source=input_source, output_handler=output_handler
        )

        # Create platform-specific controller
        platform_controller: IPlatformController = HailoPipelineController(
            config["platform"], solution
        )

        # Create platform-agnostic application
        app = VideoAnalyticsApp(config, solution, platform_controller)
        app.initialize()
        app.run()

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
