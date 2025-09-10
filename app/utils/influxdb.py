import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any
from influxdb_client_3 import InfluxDBClient3
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize the InfluxDB client
influx_client = InfluxDBClient3(
    host=settings.INFLUXDB_HOST,
    token=settings.INFLUXDB_TOKEN,
    database=settings.INFLUXDB_DATABASE
)

async def query_memory_metrics(
    device_name: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: int
) -> Dict[str, Any]:
    """
    Query memory metrics from InfluxDB for a specific device
    """
    # Convert input times to UTC for InfluxDB query
    start_time_utc = start_time.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time.astimezone(ZoneInfo("UTC"))
    
    # InfluxQL query with aggregation
    query = f"""
    SELECT
        date_bin(INTERVAL '{interval} minutes', time) AS time_window,
        mean(used) as avg_used,
        mean(free) as avg_free
    FROM memory_metrics
    WHERE 
        device_id = '{device_name}'
        AND memory_type = 'main'
        AND time >= '{start_time_utc.isoformat().replace('+00:00', 'Z')}'
        AND time <= '{end_time_utc.isoformat().replace('+00:00', 'Z')}'
    GROUP BY time_window
    ORDER BY time_window ASC
    """
    
    try:
        # Execute the query
        result = influx_client.query(query=query).to_pylist()
        
        used_series = {"name": "Mem Used", "data": []}
        free_series = {"name": "Mem Free", "data": []}
        
        # Process the results
        for row in result:
            # Parse the timestamp - using the time_window field from the query result
            timestamp_utc = row.get('time_window')
            if timestamp_utc:
                # Convert string timestamp to datetime if needed
                if isinstance(timestamp_utc, str):
                    timestamp_dt = datetime.fromisoformat(timestamp_utc.replace('Z', '+00:00'))
                else:
                    timestamp_dt = timestamp_utc
                    
                # Ensure UTC timezone
                if timestamp_dt.tzinfo is None:
                    timestamp_dt = timestamp_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                # Convert to JST
                timestamp_jst = timestamp_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                timestamp = timestamp_jst.isoformat()
                
                # Add data points
                if row.get('avg_used') is not None:
                    used_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_used'], 2)
                    })
                
                if row.get('avg_free') is not None:
                    free_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_free'], 2)
                    })
        
        return {
            "series": [used_series, free_series],
            "device_name": device_name,
            "start_time": start_time,
            "end_time": end_time,
            "interval": f"{interval}m"
        }
    except Exception as e:
        logger.error(f"Error querying memory metrics from InfluxDB: {str(e)}")
        raise


async def query_cpu_metrics(
    device_name: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: int
) -> Dict[str, Any]:
    """
    Query CPU metrics from InfluxDB for a specific device
    """
    # Convert input times to UTC for InfluxDB query
    start_time_utc = start_time.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time.astimezone(ZoneInfo("UTC"))
    # InfluxQL query with aggregation
    query = f"""
    SELECT
        date_bin(INTERVAL '{interval} minutes', time) AS time_window,
        mean(overall_cpu) as avg_overall_cpu,
        mean(overall_user) as avg_overall_user,
        mean(overall_system) as avg_overall_system
    FROM cpu_metrics
    WHERE 
        device_id = '{device_name}'
        AND time >= '{start_time_utc.isoformat().replace('+00:00', 'Z')}'
        AND time <= '{end_time_utc.isoformat().replace('+00:00', 'Z')}'
    GROUP BY time_window
    ORDER BY time_window ASC
    """
    
    try:
        # Execute the query
        result = influx_client.query(query=query).to_pylist()
        overall_series = {"name": "CPU Usage", "data": []}
        user_series = {"name": "User CPU", "data": []}
        system_series = {"name": "System CPU", "data": []}
        
        # Process the results
        for row in result:
            # Parse the timestamp - using the time_window field from the query result
            timestamp_utc = row.get('time_window')
            if timestamp_utc:
                # Convert string timestamp to datetime if needed
                if isinstance(timestamp_utc, str):
                    timestamp_dt = datetime.fromisoformat(timestamp_utc.replace('Z', '+00:00'))
                else:
                    timestamp_dt = timestamp_utc
                    
                # Ensure UTC timezone
                if timestamp_dt.tzinfo is None:
                    timestamp_dt = timestamp_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                # Convert to JST
                timestamp_jst = timestamp_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                timestamp = timestamp_jst.isoformat()
                
                # Add data points
                if row.get('avg_overall_cpu') is not None:
                    overall_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_overall_cpu'], 2)
                    })
                
                if row.get('avg_overall_user') is not None:
                    user_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_overall_user'], 2)
                    })
                
                if row.get('avg_overall_system') is not None:
                    system_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_overall_system'], 2)
                    })
        
        return {
            "series": [overall_series, user_series, system_series],
            "device_name": device_name,
            "start_time": start_time,
            "end_time": end_time,
            "interval": f"{interval}m"
        }
    except Exception as e:
        logger.error(f"Error querying CPU metrics from InfluxDB: {str(e)}")
        raise


async def query_temperature_metrics(
    device_name: str, 
    start_time: datetime, 
    end_time: datetime, 
    interval: int
) -> Dict[str, Any]:
    """
    Query temperature metrics from InfluxDB for a specific device
    """
    # Convert input times to UTC for InfluxDB query
    start_time_utc = start_time.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time.astimezone(ZoneInfo("UTC"))
    
    # InfluxQL query with aggregation
    query = f"""
    SELECT
        date_bin(INTERVAL '{interval} minutes', time) AS time_window,
        mean(cpu_celsius) as avg_cpu_temp,
        mean(gpu_celsius) as avg_gpu_temp
    FROM temperature_metrics
    WHERE 
        device_id = '{device_name}'
        AND time >= '{start_time_utc.isoformat().replace('+00:00', 'Z')}'
        AND time <= '{end_time_utc.isoformat().replace('+00:00', 'Z')}'
    GROUP BY time_window
    ORDER BY time_window ASC
    """
    
    try:
        # Execute the query
        result = influx_client.query(query=query).to_pylist()
        
        cpu_series = {"name": "CPU Temperature", "data": []}
        gpu_series = {"name": "GPU Temperature", "data": []}
        
        # Process the results
        for row in result:
            # Parse the timestamp - using the time_window field from the query result
            timestamp_utc = row.get('time_window')
            if timestamp_utc:
                # Convert string timestamp to datetime if needed
                if isinstance(timestamp_utc, str):
                    timestamp_dt = datetime.fromisoformat(timestamp_utc.replace('Z', '+00:00'))
                else:
                    timestamp_dt = timestamp_utc
                    
                # Ensure UTC timezone
                if timestamp_dt.tzinfo is None:
                    timestamp_dt = timestamp_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                # Convert to JST
                timestamp_jst = timestamp_dt.astimezone(ZoneInfo("Asia/Tokyo"))
                timestamp = timestamp_jst.isoformat()
                
                # Add data points
                if row.get('avg_cpu_temp') is not None:
                    cpu_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_cpu_temp'], 2)
                    })
                
                if row.get('avg_gpu_temp') is not None:
                    gpu_series["data"].append({
                        "timestamp": timestamp,
                        "value": round(row['avg_gpu_temp'], 2)
                    })
        
        return {
            "series": [cpu_series, gpu_series],
            "device_name": device_name,
            "start_time": start_time,
            "end_time": end_time,
            "interval": f"{interval}m"
        }
    except Exception as e:
        logger.error(f"Error querying temperature metrics from InfluxDB: {str(e)}")
        raise