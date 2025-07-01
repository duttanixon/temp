"""
Direct Database Sync Handler for CityEye Solution
"""
import os
import time
import json
import threading
import boto3
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from core.implementation.common.sqlite_manager import DatabaseManager
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import SyncError, DatabaseError, ConfigurationError
from core.implementation.common.error_handler import handle_errors

from .models import HumanResult, TrafficResult

logger = get_logger()

# PostgreSQL Database Models
Base = declarative_base()

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


class DataSyncHandler:
    """Handler for direct database synchronization of data to PostgreSQL"""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """
        Initialize the data synchronization handler
        
        Args:
            db_manager: SQLite database manager instance
            config: Synchronization configuration
        """
        self.db_manager = db_manager
        self.config = config

        # Sync configuration with defaults
        self.device_certificate_id = self._get_certificate_id()
        self.sync_batch_size = config.get("sync_batch_size", 100)
        self.sync_interval = config.get("sync_interval_seconds", 600)
        self.cleanup_interval = config.get("cleanup_interval_seconds", 3600)
        self.data_retention_days = config.get("data_retention_days", 7) 

        # AWS configuration
        self.secret_name = config.get("db_credential_secret_name")
        self.region_name = config.get("cloud", {}).get("region", "ap-northeast-1")

        # Device and solution identifiers (will be populated during sync)
        self.device_id = None
        self.solution_id = None
        self.device_solution_id = None

        # Internal state
        self.running = False
        self.sync_thread = None
        self.cleanup_thread = None
        self.last_sync_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        self.last_cleanup_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        
        logger.info(
            "DataSyncHandler initialized",
            context={
                "sync_batch_size": self.sync_batch_size,
                "sync_interval": self.sync_interval,
                "cleanup_interval": self.cleanup_interval,
                "data_retention_days": self.data_retention_days
            },
            component="DataSyncHandler"
        )

    def _get_certificate_id(self) -> str:
        """Extract certificate ID from certificate file"""
        try:
            certs_dir = self.config.get("cloud", {}).get("certs_dir", "/opt/certificates")
            cert_files = [f for f in os.listdir(certs_dir) if f.endswith(".key")]
            
            if not cert_files:
                raise ConfigurationError("No certificate file found", code="NO_CERT_FILE", source="DataSyncHandler")
            
            cert_file = cert_files[0]
            certificate_id = cert_file.split(".")[0]
            
            logger.info(f"Certificate ID extracted: {certificate_id}", component="DataSyncHandler")
            return certificate_id
            
        except Exception as e:
            logger.error("Failed to extract certificate ID", exception=e, component="DataSyncHandler")
            raise

    @handle_errors(component="DataSyncHandler")
    def _get_database_credentials(self) -> Dict[str, Any]:
        """Retrieve database credentials from AWS Secrets Manager"""
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region_name
        )
        
        try:
            response = client.get_secret_value(SecretId=self.secret_name)
            secret = json.loads(response['SecretString'])
            
            logger.info("Successfully retrieved database credentials", component="DataSyncHandler")
            return secret
            
        except ClientError as e:
            error_msg = f"Failed to retrieve database credentials: {str(e)}"
            logger.error(error_msg, exception=e, component="DataSyncHandler")
            raise DatabaseError(
                error_msg,
                code="SECRET_RETRIEVAL_FAILED",
                details={"error": str(e)},
                source="DataSyncHandler"
            ) from e

    def _create_database_connection(self) -> create_engine:
        """Create PostgreSQL database connection using credentials from Secrets Manager"""
        try:
            credentials = self._get_database_credentials()
            
            # Build connection string
            database_url = (
                f"postgresql://{credentials['username']}:{credentials['password']}"
                f"@{credentials['host']}:{credentials['port']}/{credentials['database']}"
            )
            
            # Create SQLAlchemy engine
            engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=1,         # Minimal pool size
                max_overflow=0,      # No overflow connections
                pool_recycle=300,    # Recycle connections after 5 minutes
            )
            
            logger.info("Database connection created", component="DataSyncHandler")
            return engine
            
        except Exception as e:
            error_msg = "Failed to create database connection"
            logger.error(error_msg, exception=e, component="DataSyncHandler")
            raise DatabaseError(
                error_msg,
                code="CONNECTION_FAILED",
                details={"error": str(e)},
                source="DataSyncHandler"
            ) from e

    def _initialize_device_solution_mapping(self, engine) -> None:
        """Initialize device and solution IDs from PostgreSQL database"""
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Find device by certificate ID
            device = session.query(Device).filter(
                Device.certificate_id == self.device_certificate_id
            ).first()
            
            if not device:
                raise ValueError(f"Device not found with certificate ID: {self.device_certificate_id}")
            
            self.device_id = device.device_id
            
            # Find solution
            solution_name = "City Eye"
            solution = session.query(Solution).filter(
                Solution.name == solution_name
            ).first()
            
            if not solution:
                raise ValueError(f"Solution not found with name: {solution_name}")
            
            self.solution_id = solution.solution_id
            
            # Find device-solution mapping
            device_solution = session.query(DeviceSolution).filter(
                DeviceSolution.device_id == self.device_id,
                DeviceSolution.solution_id == self.solution_id
            ).first()
            
            if not device_solution:
                raise ValueError("No device-solution mapping found")
            
            self.device_solution_id = device_solution.id
            
            logger.info(
                "Device and solution mapping initialized",
                context={
                    "device_id": str(self.device_id),
                    "solution_id": str(self.solution_id),
                    "device_solution_id": str(self.device_solution_id)
                },
                component="DataSyncHandler"
            )
            
        finally:
            session.close()

    @contextmanager
    def pg_session_scope(self, engine):
        """Provide a transactional scope for PostgreSQL operations"""
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def start(self):
        """Start the sync handler background thread"""
        if self.running:
            logger.info("Data Sync Handler is already running", component="DataSyncHandler")
            return
        
        self.running = True

        # Start sync thread
        self.sync_thread = threading.Thread(target=self._sync_worker)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()

        logger.info("DataSyncHandler started with sync and cleanup threads", component="DataSyncHandler")

    def stop(self):
        """Stop the sync and cleanup handler threads"""
        logger.info("Stopping DataSyncHandler", component="DataSyncHandler")
        self.running = False
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
            
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
            
        logger.info("DataSyncHandler stopped", component="DataSyncHandler")

    def _sync_worker(self):
        """Background worker that periodically synchronizes data"""
        logger.info("Sync worker thread started", component="DataSyncHandler")
        
        while self.running:
            try:
                now = datetime.now(ZoneInfo("Asia/Tokyo"))
                time_since_last_sync = (now - self.last_sync_time).total_seconds()
                
                if time_since_last_sync >= self.sync_interval:
                    # Process all unsynced data
                    self._process_all_unsynced_data()
                    self.last_sync_time = now
                
                # Sleep to avoid high CPU usage
                time.sleep(5)
                
            except Exception as e:
                logger.error(
                    "Error in sync worker",
                    exception=e,
                    component="DataSyncHandler"
                )
                time.sleep(30)  # Wait longer on error

    def _cleanup_worker(self):
        """Background worker that periodically cleans up synced data"""
        logger.info("Cleanup worker thread started", component="DataSyncHandler")
        
        while self.running:
            try:
                now = datetime.now(ZoneInfo("Asia/Tokyo"))
                time_since_last_cleanup = (now - self.last_cleanup_time).total_seconds()
                
                if time_since_last_cleanup >= self.cleanup_interval:
                    # Clean up old synced data
                    self._cleanup_synced_data()
                    self.last_cleanup_time = now
                
                # Sleep to avoid high CPU usage
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(
                    "Error in cleanup worker",
                    exception=e,
                    component="DataSyncHandler"
                )
                time.sleep(300)  # Wait 5 minutes on error

    @handle_errors(component="DataSyncHandler")
    def _process_all_unsynced_data(self):
        """Process all unsynced data in batches"""
        engine = None
        try:
            # Count total unsynced records
            with self.db_manager.session_scope() as session:
                total_human = session.query(HumanResult).filter_by(is_synced=False).count()
                total_traffic = session.query(TrafficResult).filter_by(is_synced=False).count()
            
            if total_human == 0 and total_traffic == 0:
                logger.info("No records to sync", component="DataSyncHandler")
                return
            
            logger.info(
                f"Starting sync process",
                context={
                    "human_records": total_human,
                    "traffic_records": total_traffic
                },
                component="DataSyncHandler"
            )

            # Create connection and initialize mappings
            engine = self._create_database_connection()
            self._initialize_device_solution_mapping(engine)

            # Process records in batches
            batch_num = 0
            total_processed = 0
            
            while True:
                if not self.running:
                    logger.info("Sync interrupted - shutting down", component="DataSyncHandler")
                    break
                
                # Fetch next batch
                human_records, traffic_records = self._fetch_batch()
                
                total_records = len(human_records) + len(traffic_records)
                if total_records == 0:
                    break
                
                # Process this batch
                batch_num += 1
                total_processed += total_records
                
                self._sync_batch_to_postgres(engine, human_records, traffic_records)
                
                # Small delay between batches
                time.sleep(0.1)
            
            logger.info(
                "Sync cycle completed",
                context={
                    "batches_processed": batch_num,
                    "records_processed": total_processed
                },
                component="DataSyncHandler"
            )
            
        except Exception as e:
            error_msg = "Error processing unsynced data"
            logger.error(error_msg, exception=e, component="DataSyncHandler")
            raise SyncError(
                error_msg,
                code="SYNC_PROCESS_FAILED",
                details={"error": str(e)},
                source="DataSyncHandler"
            ) from e
        finally:
            # Always dispose of the engine to close connections
            if engine:
                engine.dispose()
                logger.info("Database connections closed", component="DataSyncHandler")

    def _fetch_batch(self) -> Tuple[List[Dict], List[Dict]]:
        """Fetch a batch of unsynced records from SQLite"""
        human_records = []
        traffic_records = []
        
        with self.db_manager.session_scope() as session:
            # Get unsynced human results
            human_query = session.query(HumanResult).filter(
                HumanResult.is_synced == False
            ).order_by(HumanResult.timestamp).limit(self.sync_batch_size)
            
            traffic_query = session.query(TrafficResult).filter(
                TrafficResult.is_synced == False
            ).order_by(TrafficResult.timestamp).limit(self.sync_batch_size)
            
            # Collect records
            for record in human_query:
                human_records.append(record.to_dict())
            
            for record in traffic_query:
                traffic_records.append(record.to_dict())
            
            return human_records, traffic_records

    def _sync_batch_to_postgres(self, engine, human_records: List[Dict], traffic_records: List[Dict]):
        """Sync a batch of data directly to PostgreSQL"""
        try:
            with self.pg_session_scope(engine) as pg_session:
                # Process human data
                if human_records:
                    self._process_human_data(pg_session, human_records)
                
                # Process traffic data
                if traffic_records:
                    self._process_traffic_data(pg_session, traffic_records)
            
            # Mark records as synced in SQLite
            self._mark_records_synced(human_records, traffic_records)
            
            logger.info(
                "Batch synced to PostgreSQL",
                context={
                    "human_count": len(human_records),
                    "traffic_count": len(traffic_records)
                },
                component="DataSyncHandler"
            )
            
        except Exception as e:
            error_msg = "Failed to sync batch to PostgreSQL"
            logger.error(error_msg, exception=e, component="DataSyncHandler")
            raise

    def _process_human_data(self, session: Session, human_data: List[Dict]):
        """Process and update human data in PostgreSQL"""
        # Group data by hour and polygon combination
        human_data_by_group = defaultdict(lambda: {
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
        })
        
        for entry in human_data:
            try:
                # Parse timestamp and round to hour
                timestamp = datetime.fromisoformat(entry['timestamp'])
                hourly_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
                
                from_polygon = entry.get('from_polygon', 'unknown')
                to_polygon = entry.get('to_polygon', 'unknown')
                gender = entry.get('gender', '').lower()
                age = entry.get('age', '')
                
                # Create grouping key
                group_key = (hourly_timestamp, from_polygon, to_polygon)
                
                # Construct demographic field name
                field_name = f"{gender}_{age}"
                
                if field_name in human_data_by_group[group_key]:
                    human_data_by_group[group_key][field_name] += 1
                    
            except Exception as e:
                logger.error(f"Error processing human entry: {str(e)}", component="DataSyncHandler")
                continue
        
        # Insert or update records in database
        for (hourly_timestamp, from_polygon, to_polygon), counts in human_data_by_group.items():
            existing_record = session.query(CityEyeHumanTable).filter(
                CityEyeHumanTable.device_id == self.device_id,
                CityEyeHumanTable.solution_id == self.solution_id,
                CityEyeHumanTable.device_solution_id == self.device_solution_id,
                CityEyeHumanTable.timestamp == hourly_timestamp,
                CityEyeHumanTable.polygon_id_in == from_polygon,
                CityEyeHumanTable.polygon_id_out == to_polygon
            ).first()
            
            if existing_record:
                # Update existing record
                for field, value in counts.items():
                    if value > 0:
                        current_value = getattr(existing_record, field)
                        setattr(existing_record, field, current_value + value)
                session.add(existing_record)
            else:
                # Create new record
                new_record = CityEyeHumanTable(
                    data_id=uuid.uuid4(),
                    device_id=self.device_id,
                    solution_id=self.solution_id,
                    device_solution_id=self.device_solution_id,
                    timestamp=hourly_timestamp,
                    polygon_id_in=from_polygon,
                    polygon_id_out=to_polygon,
                    **counts
                )
                session.add(new_record)
    
    def _process_traffic_data(self, session: Session, traffic_data: List[Dict]):
        """Process and update traffic data in PostgreSQL"""
        # Vehicle type mapping
        VEHICLE_TYPE_MAPPING = {
            'car': 'normal',
            'truck': 'large',
            'bus': 'large',
            'bicycle': 'bicycle',
            'motorcycle': 'motorcycle'
        }
        
        # Group data by hour and polygon combination
        traffic_data_by_group = defaultdict(lambda: {
            'large': 0,
            'normal': 0,
            'bicycle': 0,
            'motorcycle': 0
        })
        
        for entry in traffic_data:
            try:
                # Parse timestamp and round to hour
                timestamp = datetime.fromisoformat(entry['timestamp'])
                hourly_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
                
                from_polygon = entry.get('from_polygon', 'unknown')
                to_polygon = entry.get('to_polygon', 'unknown')
                vehicle_type = entry.get('vehicle_type', '')
                
                # Create grouping key
                group_key = (hourly_timestamp, from_polygon, to_polygon)
                
                # Map vehicle type
                db_vehicle_category = VEHICLE_TYPE_MAPPING.get(vehicle_type.lower())
                
                if db_vehicle_category:
                    traffic_data_by_group[group_key][db_vehicle_category] += 1
                    
            except Exception as e:
                logger.error(f"Error processing traffic entry: {str(e)}", component="DataSyncHandler")
                continue
        
        # Insert or update records in database
        for (hourly_timestamp, from_polygon, to_polygon), counts in traffic_data_by_group.items():
            existing_record = session.query(CityEyeTrafficTable).filter(
                CityEyeTrafficTable.device_id == self.device_id,
                CityEyeTrafficTable.solution_id == self.solution_id,
                CityEyeTrafficTable.device_solution_id == self.device_solution_id,
                CityEyeTrafficTable.timestamp == hourly_timestamp,
                CityEyeTrafficTable.polygon_id_in == from_polygon,
                CityEyeTrafficTable.polygon_id_out == to_polygon
            ).first()
            
            if existing_record:
                # Update existing record
                for field, value in counts.items():
                    if value > 0:
                        current_value = getattr(existing_record, field)
                        setattr(existing_record, field, current_value + value)
                session.add(existing_record)
            else:
                # Create new record
                new_record = CityEyeTrafficTable(
                    data_id=uuid.uuid4(),
                    device_id=self.device_id,
                    solution_id=self.solution_id,
                    device_solution_id=self.device_solution_id,
                    timestamp=hourly_timestamp,
                    polygon_id_in=from_polygon,
                    polygon_id_out=to_polygon,
                    **counts
                )
                session.add(new_record)

    def _mark_records_synced(self, human_records: List[Dict], traffic_records: List[Dict]):
        """Mark records as synced in SQLite database"""
        with self.db_manager.session_scope() as session:
            try:
                # Mark human records as synced
                human_ids = [record["id"] for record in human_records]
                if human_ids:
                    session.query(HumanResult).filter(
                        HumanResult.id.in_(human_ids)
                    ).update({
                        "is_synced": True
                    }, synchronize_session=False)
                
                # Mark traffic records as synced
                traffic_ids = [record["id"] for record in traffic_records]
                if traffic_ids:
                    session.query(TrafficResult).filter(
                        TrafficResult.id.in_(traffic_ids)
                    ).update({
                        "is_synced": True
                    }, synchronize_session=False)
                    
            except Exception as e:
                logger.error(
                    "Error marking records as synced",
                    exception=e,
                    component="DataSyncHandler"
                )
                session.rollback()
                raise

    @handle_errors(component="DataSyncHandler")
    def _cleanup_synced_data(self):
        """Clean up old synced data from SQLite database"""
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(days=self.data_retention_days)
            
            with self.db_manager.session_scope() as session:
                # Count records to be deleted
                human_count = session.query(HumanResult).filter(
                    HumanResult.is_synced == True,
                    HumanResult.timestamp < cutoff_date
                ).count()
                
                traffic_count = session.query(TrafficResult).filter(
                    TrafficResult.is_synced == True,
                    TrafficResult.timestamp < cutoff_date
                ).count()
                
                if human_count == 0 and traffic_count == 0:
                    logger.info("No old synced records to clean up", component="DataSyncHandler")
                    return
                
                # Delete old synced human records
                if human_count > 0:
                    session.query(HumanResult).filter(
                        HumanResult.is_synced == True,
                        HumanResult.timestamp < cutoff_date
                    ).delete(synchronize_session=False)
                
                # Delete old synced traffic records
                if traffic_count > 0:
                    session.query(TrafficResult).filter(
                        TrafficResult.is_synced == True,
                        TrafficResult.timestamp < cutoff_date
                    ).delete(synchronize_session=False)
                
                # Commit happens automatically due to session_scope
                
                logger.info(
                    "Cleaned up old synced data",
                    context={
                        "human_records_deleted": human_count,
                        "traffic_records_deleted": traffic_count,
                        "retention_days": self.data_retention_days
                    },
                    component="DataSyncHandler"
                )
                
        except Exception as e:
            error_msg = "Error cleaning up synced data"
            logger.error(error_msg, exception=e, component="DataSyncHandler")
            raise SyncError(
                error_msg,
                code="CLEANUP_FAILED",
                details={"error": str(e)},
                source="DataSyncHandler"
            ) from e