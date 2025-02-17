from core.implementation.common.config_manager import ConfigManager
from core.implementation.platforms.hailo.application import HailoVideoAnalyticsApp
from core.implementation.solutions.flow_eye.solution import FlowEyeSolution
import traceback
def main():
    try:
        config_manager = ConfigManager("configs/flow-eye.yaml")
        config = config_manager.load_config()
        solution = FlowEyeSolution(config["solution"])
        app = HailoVideoAnalyticsApp(config, solution)
        # app.initialize()
        app.run()
        
    except Exception as e:
        print(traceback.format_exc())
        print(f"Error: {e}")



if __name__ == "__main__":
    main()