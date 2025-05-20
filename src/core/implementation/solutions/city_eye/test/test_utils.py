"""
Utility functions for handling test results and analysis
"""

from typing import Dict, Any, List, Optional
import os
import pandas as pd
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import DatabaseError
from core.implementation.common.error_handler import handle_errors
from core.implementation.common.sqlite_manager import DatabaseManager
from ..models import TestResult

logger = get_logger()

@handle_errors(component="TestUtils")
def get_test_results(db_manager: DatabaseManager, video_file_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get test results from the database.
    
    Args:
        db_manager: Database manager instance
        video_file_name: Optional video file name to filter results
        
    Returns:
        List of test results as dictionaries
        
    Raises:
        DatabaseError: If database operations fail
    """
    results = []
    
    with db_manager.session_scope() as session:
        try:
            query = session.query(TestResult)
            
            if video_file_name:
                query = query.filter(TestResult.video_file_name == video_file_name)
                
            for result in query.all():
                results.append(result.to_dict())
                
            return results
            
        except Exception as e:
            error_msg = "Error retrieving test results"
            logger.error(
                error_msg,
                exception=e,
                component="TestUtils"
            )
            raise DatabaseError(
                error_msg,
                code="TEST_RESULTS_QUERY_FAILED",
                details={"error": str(e)},
                source="TestUtils"
            ) from e

@handle_errors(component="TestUtils")
def export_test_results_csv(db_manager: DatabaseManager, output_path: str) -> str:
    """
    Export test results to a CSV file.
    
    Args:
        db_manager: Database manager instance
        output_path: Directory to save the CSV file
        
    Returns:
        Path to the generated CSV file
        
    Raises:
        DatabaseError: If database operations fail
    """
    try:
        # Get all test results
        results = get_test_results(db_manager)
        
        if not results:
            logger.warning("No test results to export", component="TestUtils")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Define output file path
        output_file = os.path.join(output_path, "test_results.csv")
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        logger.info(
            f"Test results exported to CSV",
            context={"file_path": output_file, "record_count": len(results)},
            component="TestUtils"
        )
        
        return output_file
        
    except Exception as e:
        error_msg = "Error exporting test results to CSV"
        logger.error(
            error_msg,
            exception=e,
            component="TestUtils"
        )
        raise DatabaseError(
            error_msg,
            code="CSV_EXPORT_FAILED",
            details={"error": str(e)},
            source="TestUtils"
        ) from e

@handle_errors(component="TestUtils")
def get_test_statistics(db_manager: DatabaseManager, video_file_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get aggregate statistics from test results.
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        Dictionary with statistics
        
    Raises:
        DatabaseError: If database operations fail
    """
    try:
        # Get all test results
        results = get_test_results(db_manager, video_file_name)
        
        if not results:
            return {
                "total_videos": 0,
                "total_human": 0,
                "total_vehicle": 0,
                "gender_ratio": {"male": 0, "female": 0},
                "age_distribution": {"less_than_18": 0,"18_to_29": 0, "30_to_49": 0, "50_to_64": 0, "65_plus": 0},
                "traffic_distribution":{"bus": 0, "car": 0, "bicycle":0, "truck": 0, "motorcycle": 0}

            }
            
        # Calculate statistics
        total_videos = len(results)
        total_human = sum(r["total_human"] for r in results)
        male_count = sum(r["male_count"] for r in results)
        female_count = sum(r["female_count"] for r in results)
        bus_count = sum(r["bus"] for r in results)
        car_count = sum(r["car"] for r in results)
        motorcycle_count = sum(r["motorcycle"] for r in results)
        bicycle_count = sum(r["bicycle"] for r in results)
        motorcycle_count = sum(r["motorcycle"] for r in results)
        truck_count = sum(r["truck"] for r in results)
        
        # Calculate gender ratio
        total_gender = male_count + female_count
        if total_gender > 0:
            gender_ratio = {
                "male": (male_count / total_gender) * 100,
                "female": (female_count / total_gender) * 100
            }
        else:
            gender_ratio = {"male": 0, "female": 0}
            
        # Calculate age distribution by gender
        # Combine all male and female counts for each age group
        male_less_than_18_count = sum(r["male_less_than_18"] for r in results)
        female_less_than_18_count = sum(r["female_less_than_18"] for r in results)
        less_than_18_count = male_less_than_18_count + female_less_than_18_count


        male_18_to_29_count = sum(r["male_18_to_29"] for r in results)
        female_18_to_29_count = sum(r["female_18_to_29"] for r in results)
        young_count = male_18_to_29_count + female_18_to_29_count
        
        male_30_to_49_count = sum(r["male_30_to_49"] for r in results)
        female_30_to_49_count = sum(r["female_30_to_49"] for r in results)
        middle_count = male_30_to_49_count + female_30_to_49_count
        
        male_50_to_64_count = sum(r["male_50_to_64"] for r in results)
        female_50_to_64_count = sum(r["female_50_to_64"] for r in results)
        senior_count = male_50_to_64_count + female_50_to_64_count
        
        male_65_plus_count = sum(r["male_65_plus"] for r in results)
        female_65_plus_count = sum(r["female_65_plus"] for r in results)
        silver_count = male_65_plus_count + female_65_plus_count
        
        total_age = less_than_18_count + young_count + middle_count + senior_count + silver_count
        
        if total_age > 0:
            age_distribution = {
                "less_than_18": (less_than_18_count / total_age) * 100,
                "18_to_29": (young_count / total_age) * 100,
                "30_to_49": (middle_count / total_age) * 100,
                "50_to_64": (senior_count / total_age) * 100,
                "65_plus": (silver_count / total_age) * 100
            }
            
            # Add gender breakdown for each age group
            age_gender_distribution = {
                "male_less_than_18": male_less_than_18_count,
                "female_less_than_18": female_less_than_18_count,
                "male_18_to_29": male_18_to_29_count,
                "female_18_to_29": female_18_to_29_count,
                "male_30_to_49": male_30_to_49_count,
                "female_30_to_49": female_30_to_49_count,
                "male_50_to_64": male_50_to_64_count,
                "female_50_to_64": female_50_to_64_count,
                "male_65_plus": male_65_plus_count,
                "female_65_plus": male_65_plus_count
            }
            traffic_distribution = {
                "bus": bus_count,
                "truck": truck_count,
                "bicycle": bicycle_count,
                "car": car_count,
                "motorcycle": motorcycle_count
            }
        else:
            age_distribution = {"less_than_18" : 0, "18_to_29": 0, "30_to_49": 0, "50_to_64": 0, "65_plus": 0}
            age_gender_distribution = {
                "male_less_than_18": 0, "female_less_than_18": 0,
                "male_18_to_29": 0, "female_18_to_29": 0,
                "male_30_to_49": 0, "female_30_to_49": 0,
                "male_50_to_64": 0, "female_50_to_64": 0,
                "male_65_plus": 0, "female_65_plus": 0
            }
            traffic_distribution = {
                "bus": 0,
                "truck": 0,
                "bicycle": 0,
                "car": 0,
                "motorcycle": 0
            }
        

            
        return {
            "total_videos": total_videos,
            "total_human": total_human,
            "gender_ratio": gender_ratio,
            "age_distribution": age_distribution,
            "age_gender_distribution": age_gender_distribution,
            "traffic_distribution": traffic_distribution,
            "videos_processed": [r["video_file_name"] for r in results]
        }
        
    except Exception as e:
        error_msg = "Error calculating test statistics"
        logger.error(
            error_msg,
            exception=e,
            component="TestUtils"
        )
        raise DatabaseError(
            error_msg,
            code="STATISTICS_CALCULATION_FAILED",
            details={"error": str(e)},
            source="TestUtils"
        ) from e