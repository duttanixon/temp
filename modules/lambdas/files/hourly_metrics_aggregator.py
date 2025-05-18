import json
import boto3
import os
from datetime import datetime, timedelta

# Initialize AWS clients
timestream_write = boto3.client('timestream-write')
timestream_query = boto3.client('timestream-query')

# Configure database and table names
DATABASE_NAME = os.environ.get('TIMESTREAM_DATABASE')
RAW_TABLE_NAME = os.environ.get('TIMESTREAM_RAW_TABLE')
HOURLY_TABLE_NAME = os.environ.get('TIMESTREAM_HOURLY_TABLE')

def aggregate_hourly_metrics():
    """Aggregate metrics to hourly intervals"""
    try:
        # Calculate time range for hourly aggregation (past hour)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        time_bucket = '1h'
        
        # Format times for query
        query_start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        query_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Aggregating metrics from {query_start_time} to {query_end_time}")
        
        # Query for CPU metrics - overall CPU
        cpu_overall_query = f"""
        SELECT 
            device_id,
            'cpu' as metric_type,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_usage,
            MAX(CAST(measure_value::double AS double)) as max_usage,
            MIN(CAST(measure_value::double AS double)) as min_usage
        FROM "{DATABASE_NAME}"."{RAW_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'cpu'
          AND metric_name = 'overall_cpu'
        GROUP BY device_id, time_bucket('{time_bucket}', time)
        """
        
        # Query for CPU metrics - per core
        cpu_core_query = f"""
        SELECT 
            device_id,
            'cpu_core' as metric_type,
            core,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_usage,
            MAX(CAST(measure_value::double AS double)) as max_usage,
            MIN(CAST(measure_value::double AS double)) as min_usage
        FROM "{DATABASE_NAME}"."{RAW_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'cpu'
          AND attribute_exists(core)
          AND metric_name = 'p_cpu'
        GROUP BY device_id, core, time_bucket('{time_bucket}', time)
        """
        
        # Query for memory metrics
        memory_query = f"""
        SELECT 
            device_id,
            'memory' as metric_type,
            memory_type,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_usage,
            MAX(CAST(measure_value::double AS double)) as max_usage,
            MIN(CAST(measure_value::double AS double)) as min_usage
        FROM "{DATABASE_NAME}"."{RAW_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'memory'
          AND measure_name = 'usage_percent'
        GROUP BY device_id, memory_type, time_bucket('{time_bucket}', time)
        """
        
        # Query for disk metrics
        disk_query = f"""
        SELECT 
            device_id,
            'disk' as metric_type,
            time_bucket('{time_bucket}', time) as period_start,
            AVG(CAST(measure_value::double AS double)) as avg_read_size,
            AVG(CAST(measure_value::double AS double)) as avg_write_size,
            SUM(CAST(measure_value::double AS double)) as total_read_size,
            SUM(CAST(measure_value::double AS double)) as total_write_size
        FROM "{DATABASE_NAME}"."{RAW_TABLE_NAME}" 
        WHERE time BETWEEN '{query_start_time}' AND '{query_end_time}'
          AND metric_type = 'disk'
        GROUP BY device_id, measure_name, time_bucket('{time_bucket}', time)
        """
        
        # Execute queries and process results
        aggregated_records = []
        
        # Process CPU overall results
        try:
            print("Executing query for overall CPU metrics")
            query_result = timestream_query.query(QueryString=cpu_overall_query)
            process_query_results(query_result, aggregated_records, 'cpu')
        except Exception as e:
            print(f"Error executing query for overall CPU metrics: {e}")
        
        # Process CPU core results
        try:
            print("Executing query for CPU core metrics")
            query_result = timestream_query.query(QueryString=cpu_core_query)
            process_query_results(query_result, aggregated_records, 'cpu_core')
        except Exception as e:
            print(f"Error executing query for CPU core metrics: {e}")
        
        # Process memory results
        try:
            print("Executing query for memory metrics")
            query_result = timestream_query.query(QueryString=memory_query)
            process_query_results(query_result, aggregated_records, 'memory')
        except Exception as e:
            print(f"Error executing query for memory metrics: {e}")
        
        # Process disk results
        try:
            print("Executing query for disk metrics")
            query_result = timestream_query.query(QueryString=disk_query)
            process_query_results(query_result, aggregated_records, 'disk')
        except Exception as e:
            print(f"Error executing query for disk metrics: {e}")
        
        # Write aggregated records to hourly table
        if aggregated_records:
            # Split records into batches of 100 (Timestream limit)
            batches = [aggregated_records[i:i + 100] for i in range(0, len(aggregated_records), 100)]
            
            for batch in batches:
                result = timestream_write.write_records(
                    DatabaseName=DATABASE_NAME,
                    TableName=HOURLY_TABLE_NAME,
                    Records=batch
                )
                print(f"Successfully wrote {len(batch)} aggregated hourly records to Timestream")
            
            return len(aggregated_records)
        else:
            print("No records to aggregate for this hour")
            return 0
    
    except Exception as e:
        print(f"Error in hourly aggregation: {e}")
        raise

def process_query_results(query_result, aggregated_records, metric_type):
    """Process query results and prepare records for Timestream"""
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
            
            # Add additional dimensions based on metric type
            if metric_type == 'cpu_core' and 'core' in data:
                dimensions.append({'Name': 'core', 'Value': data.get('core')})
            elif metric_type == 'memory' and 'memory_type' in data:
                dimensions.append({'Name': 'memory_type', 'Value': data.get('memory_type')})
            
            # Add measures based on metric type
            if metric_type in ['cpu', 'cpu_core', 'memory']:
                for measure_type in ['avg', 'max', 'min']:
                    measure_value = data.get(f'{measure_type}_usage')
                    if measure_value:
                        aggregated_records.append({
                            'Dimensions': dimensions.copy(),
                            'MeasureName': f'{measure_type}_usage_percent',
                            'MeasureValue': measure_value,
                            'MeasureValueType': 'DOUBLE',
                            'Time': str(timestamp),
                            'TimeUnit': 'MILLISECONDS'
                        })
            elif metric_type == 'disk':
                # Add disk metrics
                if 'avg_read_size' in data:
                    aggregated_records.append({
                        'Dimensions': dimensions.copy(),
                        'MeasureName': 'avg_read_size',
                        'MeasureValue': data.get('avg_read_size'),
                        'MeasureValueType': 'DOUBLE',
                        'Time': str(timestamp),
                        'TimeUnit': 'MILLISECONDS'
                    })
                if 'avg_write_size' in data:
                    aggregated_records.append({
                        'Dimensions': dimensions.copy(),
                        'MeasureName': 'avg_write_size',
                        'MeasureValue': data.get('avg_write_size'),
                        'MeasureValueType': 'DOUBLE',
                        'Time': str(timestamp),
                        'TimeUnit': 'MILLISECONDS'
                    })
                if 'total_read_size' in data:
                    aggregated_records.append({
                        'Dimensions': dimensions.copy(),
                        'MeasureName': 'total_read_size',
                        'MeasureValue': data.get('total_read_size'),
                        'MeasureValueType': 'DOUBLE',
                        'Time': str(timestamp),
                        'TimeUnit': 'MILLISECONDS'
                    })
                if 'total_write_size' in data:
                    aggregated_records.append({
                        'Dimensions': dimensions.copy(),
                        'MeasureName': 'total_write_size',
                        'MeasureValue': data.get('total_write_size'),
                        'MeasureValueType': 'DOUBLE',
                        'Time': str(timestamp),
                        'TimeUnit': 'MILLISECONDS'
                    })

def lambda_handler(event, context):
    """Lambda handler function for hourly aggregation"""
    try:
        record_count = aggregate_hourly_metrics()
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully aggregated {record_count} hourly metrics records')
        }
    
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error aggregating hourly metrics: {str(e)}')
        }
