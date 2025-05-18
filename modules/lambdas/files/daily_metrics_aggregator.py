import json
import boto3
import os
from datetime import datetime, timedelta

# Initialize AWS clients
timestream_write = boto3.client('timestream-write')
timestream_query = boto3.client('timestream-query')

# Configure database and table names
DATABASE_NAME = os.environ.get('TIMESTREAM_DATABASE')
HOURLY_TABLE_NAME = os.environ.get('TIMESTREAM_HOURLY_TABLE')
DAILY_TABLE_NAME = os.environ.get('TIMESTREAM_DAILY_TABLE')

def aggregate_daily_metrics():
    """Aggregate metrics to daily intervals"""
    try:
        # Calculate time range for daily aggregation (past day)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=1)
        time_bucket = '1d'
        
        # Format times for query
        query_start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        query_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Aggregating metrics from {query_start_time} to {query_end_time}")
        
        # Query for CPU metrics
        cpu_query = f"""
        SELECT 
            device_id,
            'cpu' as metric_type,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_usage,
            MAX(CAST(measure_value::double AS double)) as max_usage,
            MIN(CAST(measure_value::double AS double)) as min_usage
        FROM "{DATABASE_NAME}"."{HOURLY_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'cpu'
          AND measure_name = 'avg_usage_percent'
        GROUP BY device_id, time_bucket('{time_bucket}', time)
        """
        
        # Query for memory metrics
        memory_query = f"""
        SELECT 
            device_id,
            'memory' as metric_type,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_usage,
            MAX(CAST(measure_value::double AS double)) as max_usage,
            MIN(CAST(measure_value::double AS double)) as min_usage
        FROM "{DATABASE_NAME}"."{HOURLY_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'memory'
          AND measure_name = 'avg_usage_percent'
        GROUP BY device_id, time_bucket('{time_bucket}', time)
        """
        
        # Query for disk metrics
        disk_query = f"""
        SELECT 
            device_id,
            'disk' as metric_type,
            disk_name,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_usage,
            MAX(CAST(measure_value::double AS double)) as max_usage,
            MIN(CAST(measure_value::double AS double)) as min_usage
        FROM "{DATABASE_NAME}"."{HOURLY_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'disk'
          AND measure_name = 'avg_usage_percent'
        GROUP BY device_id, disk_name, time_bucket('{time_bucket}', time)
        """
        
        # Execute queries and process results
        aggregated_records = []
        
        for query, metric_type in [(cpu_query, 'cpu'), (memory_query, 'memory'), (disk_query, 'disk')]:
            try:
                print(f"Executing query for {metric_type} metrics")
                query_result = timestream_query.query(QueryString=query)
                
                # Process query results
                column_info = query_result.get('ColumnInfo', [])
                column_names = [col.get('Name') for col in column_info]
                
                for row in query_result.get('Rows', []):
                    # Parse row data
                    data = {}
                    row_data = row.get('Data', [])
                    for i, column_name in enumerate(column_names):
                        if i < len(row_data):
                            data[column_name] = row_data[i].get('ScalarValue')
                    
                    # Create Timestream record for aggregated data
                    if 'period_start' in data:
                        try:
                            timestamp = int(datetime.strptime(data.get('period_start'), '%Y-%m-%d %H:%M:%S.%f').timestamp() * 1000)
                        except ValueError:
                            timestamp = int(datetime.strptime(data.get('period_start'), '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
                        
                        dimensions = [
                            {'Name': 'device_id', 'Value': data.get('device_id', 'unknown')},
                            {'Name': 'metric_type', 'Value': data.get('metric_type', metric_type)}
                        ]
                        
                        # Add disk_name dimension for disk metrics
                        if metric_type == 'disk' and 'disk_name' in data:
                            dimensions.append({'Name': 'disk_name', 'Value': data.get('disk_name')})
                        
                        # Add records for avg, max, min
                        for measure_type in ['avg', 'max', 'min']:
                            measure_value = data.get(f'{measure_type}_usage')
                            if measure_value:
                                aggregated_records.append({
                                    'Dimensions': dimensions,
                                    'MeasureName': f'{measure_type}_usage_percent',
                                    'MeasureValue': measure_value,
                                    'MeasureValueType': 'DOUBLE',
                                    'Time': str(timestamp),
                                    'TimeUnit': 'MILLISECONDS'
                                })
            
            except Exception as e:
                print(f"Error executing query for {metric_type}: {e}")
                continue
        
        # Write aggregated records to daily table
        if aggregated_records:
            # Split records into batches of 100 (Timestream limit)
            batches = [aggregated_records[i:i + 100] for i in range(0, len(aggregated_records), 100)]
            
            for batch in batches:
                result = timestream_write.write_records(
                    DatabaseName=DATABASE_NAME,
                    TableName=DAILY_TABLE_NAME,
                    Records=batch
                )
                print(f"Successfully wrote {len(batch)} aggregated daily records to Timestream")
            
            return len(aggregated_records)
        else:
            print("No records to aggregate for this day")
            return 0
    
    except Exception as e:
        print(f"Error in daily aggregation: {e}")
        raise

def lambda_handler(event, context):
    """Lambda handler function for daily aggregation"""
    try:
        record_count = aggregate_daily_metrics()
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully aggregated {record_count} daily metrics records')
        }
    
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error aggregating daily metrics: {str(e)}')
        }