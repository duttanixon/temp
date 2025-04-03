from typing import Dict, Any
from core.interfaces.solutions.solution import ISolution
from core.interfaces.platforms.platform_controller import IPlatformController
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import ConfigurationError
from core.implementation.common.error_handler import handle_errors

logger = get_logger()

class VideoAnalyticsApp:
    """Main video analytics that orchestrates the solution and platform components
    """

    def __init__(
        self, config: Dict[str, Any], solution: ISolution, platform: IPlatformController
    ):
        """
        Initialize the video analytics application

        Args:
            config: Application configuration
            solution: Solution implementation (e.g, CityEyeSolution)
            platform: platform controller implementation
        """
        self.platform = platform
        self.config = config
        self.solution = solution
        logger.info(
            "VideoAnalyticsApp created",
            context={
                "soution_type": solution.__class__.__name__
            },
            component="VideoAnalyticsApp"
            
        )

    @handle_errors(component="VideoAnalyticsApp")
    def initialize(self) -> None:
        """
        Initialize the platform and set up the processing pipeline.

        Raises:
            ConfigurationError: If initialization fails due to configuration issues
        """
        try:
            
            # Initialize the platform
            self.platform.initialize()
            logger.info("Initialized platform controller", context={"platform_type": self.platform.__class__.__name__},component="VideoAnalyticsApp")

            #Set up the processing pipeline
            self.platform.setup_pipeline()
            
            logger.info("Video analytics Application initialized successfully", component="VideoAnalyticsApp")

        except Exception as e:
            error_msg = "Failed to initlize video analytics application"
            logger.error(
                error_msg,
                exception=e,
                component="VideoAnalyticsApp"
            )
            raise ConfigurationError(
                error_msg,
                code="APP_INIT_FAILED",
                details={"error": str(e)},
                source="VideoAnalyticsApp",
                recoverable=False
            )

    @handle_errors(component="VideoAnalyticsApp")
    def run(self) -> None:
        """
        Run the video analytics application.

        This method block untill the application exits.
        """
        try:
            logger.info("Starting video analytics application", component="VideoAnalyticsApp")

            # Run the application (this will typically block until shutdown)
            self.platform.run()

            logger.info("Video analytics application exited", component="VideoAnalyticsApp")

        except Exception as e:
            error_msg = "Error running video analytics application"
            logger.error(
                error_msg,
                exception=e,
                component="VideoAnalyticsApp"
            )
        
        finally:
            logger.info("Cleaning up resources", component="VideoAnalyticsApp")
            self.platform.cleanup()

