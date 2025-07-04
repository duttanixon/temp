import json
import base64
import gzip
import boto3  # Uncomment this - required for Timestream client
import os
import time
from datetime import datetime

# Initialize AWS clients - uncomment this
timestream_write = boto3.client('timestream-write')

# Configure database and table names
DATABASE_NAME = os.environ.get('TIMESTREAM_DATABASE')
RAW_TABLE_NAME = os.environ.get('TIMESTREAM_RAW_TABLE')

def decode_log_data(log_data):
    """Decode CloudWatch Log data from base64 gzip format"""
    compressed_payload = base64.b64decode(log_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    log_events = json.loads(uncompressed_payload)
    return log_events

def process_metric_record(record):
    """Extract metrics from CloudWatch record and format for Timestream"""
    # Extract log data
    log_events = decode_log_data(record['data'])
    
    # Get the log stream name to help determine metric type
    log_stream = log_events.get('logStream', '')
    
    records_to_write = []
    
    for event in log_events.get('logEvents', []):
        # Parse the message, which might be a JSON string
        try:
            if isinstance(event.get('message'), str):
                message = json.loads(event.get('message', '{}'))
            else:
                message = event.get('message', {})
            
            # Extract device_id from message
            device_id = message.get('device_id', 'unknown')
            
            # Extract timestamp from _aws field or use event timestamp
            timestamp = event.get('timestamp', int(time.time() * 1000))
            if '_aws' in message and 'Timestamp' in message['_aws']:
                timestamp = message['_aws']['Timestamp']
            
            # Determine metric type from log stream name
            if 'rpi.cpu' in log_stream:
                process_cpu_metrics(message, device_id, timestamp, records_to_write)
            elif 'rpi.mem' in log_stream:
                process_memory_metrics(message, device_id, timestamp, records_to_write)
            elif 'rpi.disk' in log_stream:
                process_disk_metrics(message, device_id, timestamp, records_to_write)
            
        except Exception as e:
            print(f"Error processing record: {e}")
            continue
    
    return records_to_write

def process_cpu_metrics(message, device_id, timestamp, records_to_write):
    """Process CPU metrics from the message"""
    # Process overall CPU metrics
    overall_metrics = [
        ('cpu_p', 'overall_cpu'),
        ('user_p', 'overall_user'),
        ('system_p', 'overall_system')
    ]
    
    for source_name, target_name in overall_metrics:
        if source_name in message:
            records_to_write.append({
                'Dimensions': [
                    {'Name': 'device_id', 'Value': device_id},
                    {'Name': 'metric_type', 'Value': 'cpu'},
                    {'Name': 'metric_name', 'Value': target_name}
                ],
                'MeasureName': 'usage_percent',
                'MeasureValue': str(message[source_name]),
                'MeasureValueType': 'DOUBLE',
                'Time': str(timestamp),
                'TimeUnit': 'MILLISECONDS'
            })
    
    # Process per-core CPU metrics
    for key, value in message.items():
        if key.startswith('cpu') and '.' in key and isinstance(value, (int, float)):
            parts = key.split('.')
            core = parts[0]
            metric = parts[1]
            
            records_to_write.append({
                'Dimensions': [
                    {'Name': 'device_id', 'Value': device_id},
                    {'Name': 'metric_type', 'Value': 'cpu'},
                    {'Name': 'core', 'Value': core},
                    {'Name': 'metric_name', 'Value': metric}
                ],
                'MeasureName': 'usage_percent',
                'MeasureValue': str(value),
                'MeasureValueType': 'DOUBLE',
                'Time': str(timestamp),
                'TimeUnit': 'MILLISECONDS'
            })

def process_memory_metrics(message, device_id, timestamp, records_to_write):
    """Process memory metrics from the message"""
    # Process main memory metrics
    memory_metrics = ['Mem.total', 'Mem.used', 'Mem.free']
    
    for metric in memory_metrics:
        if metric in message:
            metric_name = metric.split('.')[1]
            records_to_write.append({
                'Dimensions': [
                    {'Name': 'device_id', 'Value': device_id},
                    {'Name': 'metric_type', 'Value': 'memory'},
                    {'Name': 'memory_type', 'Value': 'main'}
                ],
                'MeasureName': metric_name,
                'MeasureValue': str(message[metric]),
                'MeasureValueType': 'DOUBLE',
                'Time': str(timestamp),
                'TimeUnit': 'MILLISECONDS'
            })
    
    # Process swap memory metrics
    swap_metrics = ['Swap.total', 'Swap.used', 'Swap.free']
    
    for metric in swap_metrics:
        if metric in message:
            metric_name = metric.split('.')[1]
            records_to_write.append({
                'Dimensions': [
                    {'Name': 'device_id', 'Value': device_id},
                    {'Name': 'metric_type', 'Value': 'memory'},
                    {'Name': 'memory_type', 'Value': 'swap'}
                ],
                'MeasureName': metric_name,
                'MeasureValue': str(message[metric]),
                'MeasureValueType': 'DOUBLE',
                'Time': str(timestamp),
                'TimeUnit': 'MILLISECONDS'
            })
    
    # Calculate memory usage percentage
    if 'Mem.total' in message and 'Mem.used' in message:
        if message['Mem.total'] > 0:
            memory_percent = (message['Mem.used'] / message['Mem.total']) * 100
            records_to_write.append({
                'Dimensions': [
                    {'Name': 'device_id', 'Value': device_id},
                    {'Name': 'metric_type', 'Value': 'memory'},
                    {'Name': 'memory_type', 'Value': 'main'}
                ],
                'MeasureName': 'usage_percent',
                'MeasureValue': str(memory_percent),
                'MeasureValueType': 'DOUBLE',
                'Time': str(timestamp),
                'TimeUnit': 'MILLISECONDS'
            })

def process_disk_metrics(message, device_id, timestamp, records_to_write):
    """Process disk metrics from the message"""
    disk_metrics = ['read_size', 'write_size']
    
    for metric in disk_metrics:
        if metric in message:
            records_to_write.append({
                'Dimensions': [
                    {'Name': 'device_id', 'Value': device_id},
                    {'Name': 'metric_type', 'Value': 'disk'}
                ],
                'MeasureName': metric,
                'MeasureValue': str(message[metric]),
                'MeasureValueType': 'DOUBLE',
                'Time': str(timestamp),
                'TimeUnit': 'MILLISECONDS'
            })

def write_to_timestream(records):
    """Write records to Timestream database"""
    if not records:
        return
    
    try:
        print(f"Writing {len(records)} records to Timestream")
        # Split records into batches of 100 (Timestream limit)
        batches = [records[i:i + 100] for i in range(0, len(records), 100)]
        
        for batch in batches:
            # Add additional error logging for debugging
            try:
                print(f"Writing batch of {len(batch)} records")
                result = timestream_write.write_records(
                    DatabaseName=DATABASE_NAME,
                    TableName=RAW_TABLE_NAME,
                    Records=batch
                )
                print(f"Successfully wrote {len(batch)} records to Timestream database {DATABASE_NAME}, table {RAW_TABLE_NAME}")
            except Exception as batch_error:
                print(f"Error writing batch to Timestream: {str(batch_error)}")
                # Print the first record for debugging
                if len(batch) > 0:
                    print(f"Sample record: {json.dumps(batch[0])}")
                raise batch_error
    
    except Exception as e:
        print(f"Error in write_to_timestream: {str(e)}")
        raise



def lambda_handler(event, context):
    """Lambda handler function"""
    try:        
        # Check if this is a direct AWS logs event
        if 'awslogs' in event:
            record = event['awslogs']
            processed_records = process_metric_record(record)
            
            # Write raw records to Timestream
            if processed_records:
                write_to_timestream(processed_records)
            
            return {
                'statusCode': 200,
                'body': json.dumps(f'Successfully processed {len(processed_records)} metrics records')
            }
        # Handle CloudWatch subscription filter format
        elif 'Records' in event:
            all_records = []
            for record in event['Records']:
                # If this is SNS notification format
                if 'Sns' in record:
                    message = json.loads(record['Sns']['Message'])
                    if 'awslogs' in message:
                        processed_records = process_metric_record(message['awslogs'])
                        all_records.extend(processed_records)
                else:
                    # Regular CloudWatch Logs format
                    processed_records = process_metric_record(record)
                    all_records.extend(processed_records)
            
            # Write all records to Timestream
            if all_records:
                write_to_timestream(all_records)
            
            return {
                'statusCode': 200,
                'body': json.dumps(f'Successfully processed {len(all_records)} metrics records')
            }
        else:
            error_msg = "Unsupported event format"
            print(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps(f'Error: {error_msg}')
            }
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing metrics: {str(e)}')
        }


