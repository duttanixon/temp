from core.implementation.common.config_manager import ConfigManager
from core.implementation.platforms.application import VideoAnalyticsApp
from core.implementation.solutions.flow_eye.solution import FlowEyeSolution
from core.implementation.platforms.hailo.flow_eye.controller import HailoPipelineController
from core.implementation.io.factories.input_factory import InputSourceFactory
from core.implementation.io.factories.output_factory import OutputHandlerFactory
import traceback

def main():
    try:
        config_manager = ConfigManager("configs/flow-eye.yaml")
        config = config_manager.load_config()

        # Create I/O handlers using factories
        input_source = InputSourceFactory.create(config["solution"]["input"])
        output_handler = OutputHandlerFactory.create(config["solution"]["output"])

        solution = FlowEyeSolution(
            config["solution"],
            input_source=input_source,
            output_handler=output_handler
        )

        # Create platform-specific controller
        platform_controller = HailoPipelineController(config, solution)

        # Create platform-agnostic application
        app = VideoAnalyticsApp(config, solution, platform_controller)
        app.run()
        
    except Exception as e:
        print(traceback.format_exc())
        print(f"Error: {e}")



if __name__ == "__main__":
    main()