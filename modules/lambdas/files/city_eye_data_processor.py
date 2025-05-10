import os
import json
import base64
import gzip
import uuid
from datetime import datetime
import boto3
from typing import Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Initialize SQLAlchemy
Base = declarative_base()

# Define minimal models needed for Lambda function
class Device(Base):
    __tablename__ = "devices"
    device_id = Column(UUID(as_uuid=True), primary_key=True)
    certificate_id = Column(String)
    name = Column(String)

class Solution(Base):
    __tablename__ = "solutions"
    solution_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String)

class DeviceSolution(Base):
    __tablename__ = "device_solutions"
    id = Column(UUID(as_uuid=True), primary_key=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"))
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"))

class CityEyeHumanTable(Base):
    __tablename__ = "city_eye_human_data"
    
    data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    device_solution_id = Column(UUID(as_uuid=True), ForeignKey("device_solutions.id"), nullable=False)

    timestamp = Column(DateTime, nullable=False)
    polygon_id_in = Column(String, nullable=False)
    polygon_id_out = Column(String, nullable=False)
    male_less_than_18 = Column(Integer, nullable=False, default=0)
    female_less_than_18 = Column(Integer, nullable=False, default=0)
    male_18_to_29 = Column(Integer, nullable=False, default=0)
    female_18_to_29 = Column(Integer, nullable=False, default=0)
    male_30_to_49 = Column(Integer, nullable=False, default=0)
    female_30_to_49 = Column(Integer, nullable=False, default=0)
    male_50_to_64 = Column(Integer, nullable=False, default=0)
    female_50_to_64 = Column(Integer, nullable=False, default=0)
    male_65_plus = Column(Integer, nullable=False, default=0)
    female_65_plus = Column(Integer, nullable=False, default=0)


class CityEyeTrafficTable(Base):
    __tablename__ = "city_eye_traffic_data"
    
    data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.device_id"), nullable=False)
    solution_id = Column(UUID(as_uuid=True), ForeignKey("solutions.solution_id"), nullable=False)
    device_solution_id = Column(UUID(as_uuid=True), ForeignKey("device_solutions.id"), nullable=False)

    timestamp = Column(DateTime, nullable=False)
    polygon_id_in = Column(String, nullable=False)
    polygon_id_out = Column(String, nullable=False)
    large = Column(Integer, nullable=False, default=0)
    normal = Column(Integer, nullable=False, default=0)
    bicycle = Column(Integer, nullable=False, default=0)
    motorcycle = Column(Integer, nullable=False, default=0)


def truncate_to_hour(timestamp):
    """
    Truncate timestamp to the hour (YYYY-MM-DD HH:00:00)
    """
    return timestamp.replace(minute=0, second=0, microsecond=0)

def process_human_data(session, human_data, device_id, solution_id, device_solution_id):
    """
    Process human data entries and insert into the CityEyeHumanTable
    """
    # Group data by hourly timestamp, polygon_in, polygon_out to consolidate entries
    human_data_by_group = {}
    for entry in human_data:
        # Extract data from the entry
        entry_id = entry.get('id')
        from_polygon = entry.get('from_polygon')
        to_polygon = entry.get('to_polygon')
        gender = entry.get('gender')
        age = entry.get('age')
        timestamp_str = entry.get('timestamp')

        # Skip entries with missing required fields
        if not all([from_polygon, to_polygon, gender, age, timestamp_str]):
            print(f"Skipping human entry with missing fields: {entry}")
            continue

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            # Truncate to hour for hourly aggregation
            hourly_timestamp = truncate_to_hour(timestamp)
        except (ValueError, TypeError):
            print(f"Invalid timestamp format: {timestamp_str}")
            continue
        except Exception as e:
            print(f"Error processing traffic entry: {str(e)}")
            continue

        # Create a key for grouping
        group_key = (hourly_timestamp, from_polygon, to_polygon)

        if group_key not in human_data_by_group:
            human_data_by_group[group_key] = {
                'male_less_than_18': 0,
                'female_less_than_18': 0,
                'male_18_to_29': 0,
                'female_18_to_29': 0,
                'male_30_to_49': 0,
                'female_30_to_49': 0,
                'male_50_to_64': 0,
                'female_50_to_64': 0,
                'male_65_plus': 0,
                'female_65_plus': 0
            }
        
        # Map age category to database age group
        # Construct demographic field name (e.g., 'male_18_to_29')
        field_name = f"{gender}_{age}"

        if field_name in human_data_by_group[group_key]:
            human_data_by_group[group_key][field_name] += 1
        else:
            print(f"Warning: Unrecognized demographic combination: {gender}_{age}")
    
    for (hourly_timestamp, from_polygon, to_polygon), counts in human_data_by_group.items():
        # Check if a record already exists for this timestamp and polygon combination
        existing_record = session.query(CityEyeHumanTable).filter(
            CityEyeHumanTable.device_id == device_id,
            CityEyeHumanTable.solution_id == solution_id,
            CityEyeHumanTable.device_solution_id == device_solution_id,
            CityEyeHumanTable.timestamp == hourly_timestamp,
            CityEyeHumanTable.polygon_id_in == from_polygon,
            CityEyeHumanTable.polygon_id_out == to_polygon
        ).first()

        if existing_record:
            # Update existing record
            for field, value in counts.items():
                if value > 0:  # Only update fields with non-zero values
                    current_value = getattr(existing_record, field)
                    setattr(existing_record, field, current_value + value)
            session.add(existing_record)

        else:
            # Create new record
            new_record = CityEyeHumanTable(
                data_id=uuid.uuid4(),
                device_id=device_id,
                solution_id=solution_id,
                device_solution_id=device_solution_id,
                timestamp=hourly_timestamp,
                polygon_id_in=from_polygon,
                polygon_id_out=to_polygon,
                **counts
            )
            session.add(new_record)


def process_traffic_data(session, traffic_data, device_id, solution_id, device_solution_id):
    """
    Process traffic data entries and insert into the CityEyeTrafficTable
    """
    # Group data by hourly timestamp, polygon_in, polygon_out to consolidate entries
    traffic_data_by_group = {}

    for entry in traffic_data:
        # Extract data from the entry
        entry_id = entry.get('id')
        from_polygon = entry.get('from_polygon')
        to_polygon = entry.get('to_polygon')
        vehicle_type = entry.get('vehicletype')
        timestamp_str = entry.get('timestamp')

        # Skip entries with missing required fields
        if not all([from_polygon, to_polygon, vehicle_type, timestamp_str]):
            print(f"Skipping traffic entry with missing fields: {entry}")
            continue
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            # Truncate to hour for hourly aggregation
            hourly_timestamp = truncate_to_hour(timestamp)
        except (ValueError, TypeError):
            print(f"Invalid timestamp format: {timestamp_str}")
            continue
        except Exception as e:
            print(f"Error processing traffic entry: {str(e)}")
            continue

        # Create a key for grouping
        group_key = (hourly_timestamp, from_polygon, to_polygon)
        
        # Initialize counter dictionary if this is a new group
        if group_key not in traffic_data_by_group:
            traffic_data_by_group[group_key] = {
                'large': 0,
                'normal': 0,
                'bicycle': 0,
                'motorcycle': 0
            }

        # Increment the counter for this vehicle type
        if vehicle_type in traffic_data_by_group[group_key]:
            traffic_data_by_group[group_key][vehicle_type] += 1
        else:
            print(f"Warning: Unrecognized vehicle type: {vehicle_type}")

    # Insert or update records in the database
    for (hourly_timestamp, from_polygon, to_polygon), counts in traffic_data_by_group.items():
        # Check if a record already exists for this timestamp and polygon combination
        existing_record = session.query(CityEyeTrafficTable).filter(
            CityEyeTrafficTable.device_id == device_id,
            CityEyeTrafficTable.solution_id == solution_id,
            CityEyeTrafficTable.device_solution_id == device_solution_id,
            CityEyeTrafficTable.timestamp == hourly_timestamp,
            CityEyeTrafficTable.polygon_id_in == from_polygon,
            CityEyeTrafficTable.polygon_id_out == to_polygon
        ).first()
        
        if existing_record:
            # Update existing record
            for field, value in counts.items():
                if value > 0:  # Only update fields with non-zero values
                    current_value = getattr(existing_record, field)
                    setattr(existing_record, field, current_value + value)
            session.add(existing_record)
        else:
            # Create new record
            new_record = CityEyeTrafficTable(
                data_id=uuid.uuid4(),
                device_id=device_id,
                solution_id=solution_id,
                device_solution_id=device_solution_id,
                timestamp=hourly_timestamp,
                polygon_id_in=from_polygon,
                polygon_id_out=to_polygon,
                **counts
            )
            session.add(new_record)

def decode_cloud_message(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        # Check if the message is compressed
        if message.get("compressed", False):
            # Decode the base64 string
            encoded_data = message.get("data", "")
            if not encoded_data:
                raise ValueError("No data field in compressed message")
            
            # Decode base64
            compressed_data = base64.b64decode(encoded_data)
            
            # Decompress with gzip
            decompressed_data = gzip.decompress(compressed_data)
            
            # Parse the JSON data
            decoded_data = json.loads(decompressed_data.decode('utf-8'))
            
            print(f"Decoded data conpleted")
            return decoded_data
        else:
            # If not compressed, just log the raw event
            print("Message is not compressed, processing raw event")
            return message
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        raise ValueError(f"Error processing message: {str(e)}")


def lambda_handler(event, context):
    """
    Lambda function to process IoT Core messages from the City Eye system

    Args:
        event (dict): The IoT Core message data including client_id and solution_name
        context(object): Lambda context object
    
    Returns:
        dict: Response with status code and message
    """
    try:
        # Get environment information
        environment = os.environ.get('ENVIRONMENT', 'unknown')
        print(f"Environment: {environment}")
        
        decoded_data = decode_cloud_message(event)
            
        # Get database URL from environment variable
        # to do - use secrets using AWS Secrets Manager
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("Neither DATABASE_URL nor DB_SECRET_NAME environment variable is set")

        # Extract data from the event
        device_id_str = decoded_data.get('deviceID')  # This is certificate_id in the database
        solution_type = decoded_data.get('solutionType')
        message_timestamp = decoded_data.get('timestamp')
        payload = decoded_data.get('payload', {})
        
        print(f"Processing message from device certificate ID: {device_id_str}, solution: {solution_type}")

        # Extract data from payload
        human_data = payload.get('human_data', [])
        traffic_data = payload.get('traffic_data', [])
        
        print(f"Found {len(human_data)} human data entries and {len(traffic_data)} traffic data entries")
        
        # Connect to the database
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Find the device in the database by certificate_id
            device = session.query(Device).filter(Device.certificate_id == device_id_str).first()
            
            if not device:
                raise ValueError(f"Device not found with certificate ID: {device_id_str}")
            
            # Find the solution in the database
            solution_name = event.get('solution_name')
            solution = session.query(Solution).filter(Solution.name == solution_name).first()

            if not solution:
                raise ValueError(f"Solution not found with name: {solution_name}")
            
            # Find the device-solution mapping
            device_solution = session.query(DeviceSolution).filter(
                DeviceSolution.device_id == device.device_id,
                DeviceSolution.solution_id == solution.solution_id
            ).first()
            
            if not device_solution:
                raise ValueError(f"No device-solution mapping found for device {device.name} and solution {solution.name}")                   

            # Process human data
            if human_data:
                process_human_data(session, human_data, device.device_id, solution.solution_id, device_solution.id)
            
            # Process traffic data
            if traffic_data:
                process_traffic_data(session, traffic_data, device.device_id, solution.solution_id, device_solution.id)

            # Commit changes to the database
            session.commit()
            print("Data successfully written to database")

        except Exception as e:
            session.rollback()
            print(f"Database operation failed: {str(e)}")
            raise e
        finally:
            session.close()

    except Exception as e:
        print(f"Error processing message: {str(e)}")
        raise ValueError(f"Error processing message: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed City Eye IoT data')
    }