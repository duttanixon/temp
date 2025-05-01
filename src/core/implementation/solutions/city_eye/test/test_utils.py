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
def get_test_statistics(db_manager: DatabaseManager) -> Dict[str, Any]:
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
        results = get_test_results(db_manager)
        
        if not results:
            return {
                "total_videos": 0,
                "total_human": 0,
                "total_vehicle": 0,
                "gender_ratio": {"male": 0, "female": 0},
                "age_distribution": {"young": 0, "middle": 0, "senior": 0, "silver": 0},
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
        male_young_count = sum(r["male_young"] for r in results)
        female_young_count = sum(r["female_young"] for r in results)
        young_count = male_young_count + female_young_count
        
        male_middle_count = sum(r["male_middle"] for r in results)
        female_middle_count = sum(r["female_middle"] for r in results)
        middle_count = male_middle_count + female_middle_count
        
        male_senior_count = sum(r["male_senior"] for r in results)
        female_senior_count = sum(r["female_senior"] for r in results)
        senior_count = male_senior_count + female_senior_count
        
        male_silver_count = sum(r["male_silver"] for r in results)
        female_silver_count = sum(r["female_silver"] for r in results)
        silver_count = male_silver_count + female_silver_count
        
        total_age = young_count + middle_count + senior_count + silver_count
        
        if total_age > 0:
            age_distribution = {
                "young": (young_count / total_age) * 100,
                "middle": (middle_count / total_age) * 100,
                "senior": (senior_count / total_age) * 100,
                "silver": (silver_count / total_age) * 100
            }
            
            # Add gender breakdown for each age group
            age_gender_distribution = {
                "male_young": male_young_count,
                "female_young": female_young_count,
                "male_middle": male_middle_count,
                "female_middle": female_middle_count,
                "male_senior": male_senior_count,
                "female_senior": female_senior_count,
                "male_silver": male_silver_count,
                "female_silver": female_silver_count
            }
            traffic_distribution = {
                "bus": bus_count,
                "truck": truck_count,
                "bicycle": bicycle_count,
                "car": car_count,
                "motorcycle": motorcycle_count
            }
        else:
            age_distribution = {"young": 0, "middle": 0, "senior": 0, "silver": 0}
            age_gender_distribution = {
                "male_young": 0, "female_young": 0,
                "male_middle": 0, "female_middle": 0,
                "male_senior": 0, "female_senior": 0,
                "male_silver": 0, "female_silver": 0
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