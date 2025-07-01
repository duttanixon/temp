"""
Database operations module for CityEye solution.
Handles all database write operations.
"""
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from core.implementation.common.sqlite_manager import DatabaseManager
from core.interfaces.io.input_source import IInputSource
from core.implementation.solutions.city_eye.models import HumanResult, TrafficResult, TestResult
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import DatabaseError


logger = get_logger()


class DatabaseOperations:
    """Manages database operations for the CityEye solution."""

    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager, input_source: IInputSource) -> None:
        """
        Initialize database operations manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.component_name = self.__class__.__name__
        self.db_manager = db_manager
        self.input_source = input_source
        self.test_mode = config.get("test", False)

        if self.test_mode:
            self.video_file_name = self._get_video_file_name()
            self.test_counts = self._get_test_counts()

        
        logger.info(
            "DatabaseOperations initialized",
            component=self.component_name
        )

    def _get_video_file_name(self) -> str:
        input_props = self.input_source.get_properties()
        if input_props.get("type") == "file":
            logger.info(
                "Running in test mode",
                context={"video_file": self.video_file_name},
                component=self.component_name
            )
            return os.path.basename(input_props.get("path", "unknown"))
        else:
            logger.warning(
                "Test mode is enabled but input is not a file",
                component=self.component_name
            )
            return "live_feed"

    def _get_test_counts(self) -> Dict[str, int]:

        return {
            "total_human": 0,
            "male_less_than_18": 0, "female_less_than_18": 0,
            "male_18_to_29": 0, "female_18_to_29": 0,
            "male_30_to_49": 0, "female_30_to_49": 0,
            "male_50_to_64": 0, "female_50_to_64": 0,
            "male_65_plus": 0, "female_65_plus": 0,
            "total_vehicles": 0, "bicycle": 0, "car": 0,
            "motorcycle": 0, "bus": 0, "truck": 0
        }   

    def write_frame_results(self, frame_result:Optional[Tuple[str,str]]) -> Optional[bool]:
        """
        Write cityeye results t local database.

        Args:
            frame_result: Tuple containing route and class information
        
        Raises:
            DatabaseError: If database operations fail
        """
        if not frame_result:
            return False

        route, class_ = frame_result
        try:
            from_polygon_str, to_polygon_str = route.split("->")
        except ValueError:
            logger.warning(f"Invalid route format: {route}. Expected 'from->to'. Skipping database write.", component=self.component_name)
            return False

        with self.db_manager.session_scope() as session:
            try:
                item = None
                if "vehicle" in class_:
                    vehicle_type = class_.split("::")[-1]
                    item = TrafficResult(
                        from_polygon=from_polygon_str,
                        to_polygon=to_polygon_str,
                        vehicletype= vehicle_type
                    )
                    # Update test counts if in test mode for traffic
                    if self.test_mode:
                        self.test_counts["total_vehicles"] += 1
                        # Update the vehicle type counter
                        if vehicle_type in self.test_counts:
                            self.test_counts[vehicle_type] += 1
                else:
                    gender, age = class_.split("::")
                    item = HumanResult(
                        from_polygon=from_polygon_str,
                        to_polygon=to_polygon_str,
                        gender=gender,
                        age=age
                    )
                    # Update test counts if in test mode
                    if self.test_mode:
                        self.test_counts["total_human"] += 1
                        # Update the combined gender-age counter
                        gender_age_key = f"{gender}_{age}"
                        self.test_counts[gender_age_key] += 1

                if item:
                    session.add(item)
            except Exception as e:
                logger.error(
                    "Database error",
                    exception=e,
                    context={"route": route, "class": class_},
                    component=self.component_name
                )
                session.rollback()

    def update_test_results(self) -> None:
        """
        Update test results in database when in test mode.
        Called during cleanup to ensure final counts are stored.
        """
        if not self.test_mode or (self.test_counts["total_human"] == 0 and self.test_counts["total_vehicles"] == 0):
            return
        
        try:
            logger.info(
                "Updating test results",
                context={
                    "video_file": self.video_file_name,
                    "total_human": self.test_counts["total_human"],
                    "total_vehicles": self.test_counts["total_vehicles"]
                },
                component=self.component_name
            )            

            with self.db_manager.session_scope() as session:
                # Check if entry already exists for this video file
                existing = session.query(TestResult).filter_by(
                    video_file_name=self.video_file_name
                ).first()

                if existing:
                    # Update existing human record
                    existing.total_huamn = self.test_counts["total_human"]
                    existing.male_less_than_18 = self.test_counts["male_less_than_18"]
                    existing.female_less_than_18 = self.test_counts["female_less_than_18"]
                    existing.male_18_to_29 = self.test_counts["male_18_to_29"]
                    existing.female_18_to_29 = self.test_counts["female_18_to_29"]
                    existing.male_30_to_49 = self.test_counts["male_30_to_49"]
                    existing.female_30_to_49 = self.test_counts["female_30_to_49"]
                    existing.male_50_to_64 = self.test_counts["male_50_to_64"]
                    existing.female_50_to_64 = self.test_counts["female_50_to_64"]
                    existing.male_65_plus = self.test_counts["male_65_plus"]
                    existing.female_65_plus = self.test_counts["female_65_plus"]

                    # Update existing vehicle record
                    existing.total_vehicles = self.test_counts["total_vehicles"]
                    existing.bicycle = self.test_counts["bicycle"]
                    existing.car = self.test_counts["car"]
                    existing.motorcycle = self.test_counts["motorcycle"]
                    existing.bus = self.test_counts["bus"]
                    existing.truck = self.test_counts["truck"]

                    
                else:
                    # Create new record
                    test_result = TestResult(
                        video_file_name=self.video_file_name,
                        total_human=self.test_counts["total_human"],
                        male_less_than_18=self.test_counts["male_less_than_18"],
                        female_less_than_18=self.test_counts["female_less_than_18"],
                        male_18_to_29=self.test_counts["male_18_to_29"],
                        female_18_to_29=self.test_counts["female_18_to_29"],
                        male_30_to_49=self.test_counts["male_30_to_49"],
                        female_30_to_49=self.test_counts["female_30_to_49"],
                        male_50_to_64=self.test_counts["male_50_to_64"],
                        female_50_to_64=self.test_counts["female_50_to_64"],
                        male_65_plus=self.test_counts["male_65_plus"],
                        female_65_plus=self.test_counts["female_65_plus"],
                        total_vehicles = self.test_counts["total_vehicles"],
                        bicycle = self.test_counts["bicycle"],
                        car = self.test_counts["car"],
                        motorcycle = self.test_counts["motorcycle"],
                        bus = self.test_counts["bus"],
                        truck = self.test_counts["truck"]
                    )
                    session.add(test_result)
                    session.commit()
            logger.info(
                "Test result update completed",
                context={
                    "video_file": self.video_file_name,
                    "total_human": self.test_counts["total_human"],
                    "total_vehicles": self.test_counts["total_vehicles"]
                },
                component=self.component_name
            )   
                
        except Exception as e:
            logger.error(
                "Error updating test results",
                exception=e,
                component=self.component_name
            )