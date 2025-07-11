import boto3
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Timestream client
timestream_query = boto3.client(
    'timestream-query',
    region_name = settings.AWS_REGION,
    aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY    
    )

# Get database and table names from environment variables
DATABASE_NAME = settings.TIMESTREAM_DATABASE
RAW_TABLE_NAME = settings.TIMESTREAM_RAW_TABLE

def query_memory_metrics(
    device_name: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: int
) -> Dict[str, Any]:
    """
    Query memory metrics from Timestream for a specific device
    """
    # Convert input times to UTC for Timestream query
    start_time_utc = start_time.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time.astimezone(ZoneInfo("UTC"))
    interval_seconds = interval * 60
    query = f"""
    SELECT 
        bin(time, {interval_seconds}s) as time_bin, 
        measure_name, 
        ROUND(AVG(measure_value::double), 2) as avg_value
    FROM 
        "{DATABASE_NAME}"."{RAW_TABLE_NAME}"
    WHERE 
        time BETWEEN from_iso8601_timestamp('{start_time_utc.isoformat()}') AND from_iso8601_timestamp('{end_time_utc.isoformat()}')
        AND device_id = '{device_name}'
        AND metric_type = 'memory'
        AND memory_type = 'main'
        AND measure_name IN ('used', 'free')
    GROUP BY 
        bin(time, {interval_seconds}s),
        measure_name
    ORDER BY 
        time_bin ASC,
        measure_name
    """

    try:
        response = timestream_query.query(QueryString=query)
        
        used_series = {"name": "Mem Used", "data": []}
        free_series = {"name": "Mem Free", "data": []}
        
        for row in response['Rows']:
            if len(row['Data']) >= 3:
                # Parse the UTC timestamp
                timestamp_str = row['Data'][0]['ScalarValue']
                # Convert to datetime (assuming it's in UTC)
                try:
                    # Format without timezone, assume UTC
                    timestamp_dt = datetime.fromisoformat(timestamp_str)
                    timestamp_dt = timestamp_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                    # Convert to JST
                    timestamp_jst = timestamp_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                    # Format with timezone info
                    timestamp = timestamp_jst.isoformat()
                except ValueError:
                    # If parsing fails, keep the original timestamp but log warning
                    logger.warning(f"Could not parse timestamp: {timestamp_str}")
                    timestamp = timestamp_str

                measure_name = row['Data'][1]['ScalarValue']
                value = float(row['Data'][2]['ScalarValue'])
                
                data_point = {"timestamp": timestamp, "value": value}
                
                if measure_name == 'used':
                    used_series["data"].append(data_point)
                elif measure_name == 'free':
                    free_series["data"].append(data_point)
        
        return {
            "series": [used_series, free_series],
            "device_name": device_name,
            "start_time": start_time,
            "end_time": end_time,
            "interval": f"{interval}m"
        }
    except Exception as e:
        logger.error(f"Error querying memory metrics: {str(e)}")
        raise


def query_cpu_metrics(
    device_name: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: int
) -> Dict[str, Any]:
    """
    Query CPU metrics from Timestream for a specific device
    """
    start_time_utc = start_time.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time.astimezone(ZoneInfo("UTC"))
    interval_seconds = interval * 60
    
    query = f"""
    SELECT 
        bin(time, {interval_seconds}s) as time_bin, 
        metric_name,
        ROUND(AVG(measure_value::double), 2) as avg_value
    FROM 
        "{DATABASE_NAME}"."{RAW_TABLE_NAME}"
    WHERE 
        time BETWEEN from_iso8601_timestamp('{start_time_utc.isoformat()}') AND from_iso8601_timestamp('{end_time_utc.isoformat()}')
        AND device_id = '{device_name}'
        AND metric_type = 'cpu'
        AND measure_name = 'usage_percent'
        AND metric_name IN ('overall_cpu', 'overall_user', 'overall_system')
    GROUP BY 
        bin(time, {interval_seconds}s),
        metric_name
    ORDER BY 
        time_bin ASC,
        metric_name
    """
    
    try:
        response = timestream_query.query(QueryString=query)
        
        overall_series = {"name": "CPU Usage", "data": []}
        user_series = {"name": "User CPU", "data": []}
        system_series = {"name": "System CPU", "data": []}
        
        for row in response['Rows']:
            if len(row['Data']) >= 3:
                # Parse the UTC timestamp
                timestamp_str = row['Data'][0]['ScalarValue']
                # Convert to datetime (assuming it's in UTC)
                try:
                    # Format without timezone, assume UTC
                    timestamp_dt = datetime.fromisoformat(timestamp_str)
                    timestamp_dt = timestamp_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                    # Convert to JST
                    timestamp_jst = timestamp_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                    # Format with timezone info
                    timestamp = timestamp_jst.isoformat()
                except ValueError:
                    # If parsing fails, keep the original timestamp but log warning
                    logger.warning(f"Could not parse timestamp: {timestamp_str}")
                    timestamp = timestamp_str
                metric_name = row['Data'][1]['ScalarValue']
                value = float(row['Data'][2]['ScalarValue'])
                
                data_point = {"timestamp": timestamp, "value": value}
                
                if metric_name == 'overall_cpu':
                    overall_series["data"].append(data_point)
                elif metric_name == 'overall_user':
                    user_series["data"].append(data_point)
                elif metric_name == 'overall_system':
                    system_series["data"].append(data_point)
        
        return {
            "series": [overall_series, user_series, system_series],
            "device_name": device_name,
            "start_time": start_time,
            "end_time": end_time,
            "interval": f"{interval}m"
        }
    except Exception as e:
        logger.error(f"Error querying CPU metrics: {str(e)}")
        raise

def query_temperature_metrics(
    device_name: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: int
) -> Dict[str, Any]:
    """
    Query temperature metrics from Timestream for a specific device
    """
    start_time_utc = start_time.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time.astimezone(ZoneInfo("UTC"))
    interval_seconds = interval * 60
    
    query = f"""
    SELECT 
        bin(time, {interval_seconds}s) as time_bin, 
        sensor,
        ROUND(AVG(measure_value::double), 2) as avg_value
    FROM 
        "{DATABASE_NAME}"."{RAW_TABLE_NAME}"
    WHERE 
        time BETWEEN from_iso8601_timestamp('{start_time_utc.isoformat()}') AND from_iso8601_timestamp('{end_time_utc.isoformat()}')
        AND device_id = '{device_name}'
        AND metric_type = 'temperature'
        AND measure_name = 'temperature_celsius'
        AND sensor IN ('cpu', 'gpu')
    GROUP BY 
        bin(time, {interval_seconds}s),
        sensor
    ORDER BY 
        time_bin ASC,
        sensor
    """
    
    try:
        response = timestream_query.query(QueryString=query)
        
        cpu_series = {"name": "CPU Temperature", "data": []}
        gpu_series = {"name": "GPU Temperature", "data": []}
        
        for row in response['Rows']:
            if len(row['Data']) >= 3:
                # Parse the UTC timestamp
                timestamp_str = row['Data'][0]['ScalarValue']
                # Convert to datetime (assuming it's in UTC)
                try:
                    # Format without timezone, assume UTC
                    timestamp_dt = datetime.fromisoformat(timestamp_str)
                    timestamp_dt = timestamp_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                    # Convert to JST
                    timestamp_jst = timestamp_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                    # Format with timezone info
                    timestamp = timestamp_jst.isoformat()
                except ValueError:
                    # If parsing fails, keep the original timestamp but log warning
                    logger.warning(f"Could not parse timestamp: {timestamp_str}")
                    timestamp = timestamp_str
                    
                sensor = row['Data'][1]['ScalarValue']
                value = float(row['Data'][2]['ScalarValue'])
                
                data_point = {"timestamp": timestamp, "value": value}
                
                if sensor == 'cpu':
                    cpu_series["data"].append(data_point)
                elif sensor == 'gpu':
                    gpu_series["data"].append(data_point)
        
        return {
            "series": [cpu_series, gpu_series],
            "device_name": device_name,
            "start_time": start_time,
            "end_time": end_time,
            "interval": f"{interval}m"
        }
    except Exception as e:
        logger.error(f"Error querying temperature metrics: {str(e)}")
        raise