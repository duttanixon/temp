import time
import json
import gzip
import base64
import random
import traceback
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.implementation.common.sqlite_manager import DatabaseManager
from core.interfaces.cloud.cloud_connector import ICloudConnector
from core.implementation.common.logger import get_logger
from core.implementation.common.exceptions import SyncError, DatabaseError, CloudError
from core.implementation.common.error_handler import handle_errors

from .models import HumanResult, TrafficResult


logger = get_logger()


class BatchSyncHandler:
    """Handler for batch sychonization of data to the cloud"""

    def __init__(self, db_manager: DatabaseManager, cloud_connector:ICloudConnector, config: Dict[str, Any]):
        """
        Initialize the batch synchonization handler

        Args:
            db_manager: Database manager instance
            cloud_connector: Cloud connector instance
            config: Synchonization configuration
        """
        self.db_manager = db_manager
        self.cloud_connector = cloud_connector

        # Sync configuration with defaults
        self.device_id = config.get("device_id", "unknown_device")
        self.sync_batch_size = config.get("sync_batch_size", 100)
        self.sync_interval = config.get("sync_interval_seconds", 120)
        self.max_retries = config.get("max_retries", 5)
        self.initial_backoff = config.get("initial_backoff_seconds", 2)
        self.compression_enabled = config.get("enable_compression", True)
        self.sync_topic = config.get("sync_topic", "device/ai-data/batch")


        # Internal State
        self.running = False
        self.sync_thread = None
        self.last_sync_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        self.retry_count = {} # Track retry attempts by batch_id 

    def start(self):
        """Start the sync manager background thread"""
        if self.running:
            logger.info("Sync Handler is already running", component="BatchSyncHandler")
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_worker)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        logger.info(
            "BatchSyncHandler started",
            context={
                "device_id": self.device_id,
                "sync_batch_size": self.sync_batch_size,
                "sync_interval": self.sync_interval
            },
            component="BatchSyncHandler"
        )


    def stop(self):
        """Stop the sync handler thread"""
        logger.info("Stopping BatchSyncHandler", component="BatchSyncHandler")
        self.running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        logger.info("BatchSyncHandler stopped", component="BatchSyncHandler")
    
    def _sync_worker(self):
        """Background worker that periodically synchonizes data"""
        logger.info("Sync worker thread started", component="BatchSyncHandler")

        while self.running:
            try:
                # Check if it's time to sync
                now = datetime.now(ZoneInfo("Asia/Tokyo"))
                time_since_last_sync = (now - self.last_sync_time).total_seconds()

                if time_since_last_sync >= self.sync_interval:
                    # Process all unsynced data in batches
                    self._process_all_unsynced_data()
                    self.last_sync_time = now
                    self.cleanup_stale_processing()


                # sleep a bit to avoiud high cpu usage                
                time.sleep(2)
            
            except Exception as e:
                logger.error(
                    "Error in sync worker",
                    exception=e,
                    component="BatchSyncHandler"
                )
                time.sleep(5)
    
    @handle_errors(component="BatchSyncHandler")
    def _process_all_unsynced_data(self):
        """Process all unsynced data in batches
        Raises:        
            SyncError: If synchronization fails        
        """
        try:
            # First, count total unsynced records
            with self.db_manager.session_scope() as session:
                try:
                    total_human = session.query(HumanResult).filter_by(is_synced=False, is_processing=False).count()
                    total_traffic = session.query(TrafficResult).filter_by(is_synced=False, is_processing=False).count()
                except Exception as e:
                    logger.error("Error occured during database operation", exception=e, component="BatchSyncHandler")
                    session.rollback()
                    return

            if total_human == 0 and total_traffic == 0:
                logger.info("No records to sync", component="BatchSyncHandler")
                return
            
            # Process records 

            batch_num = 0
            total_processed = 0

            while True:
                if not self.running:
                    logger.info("Sync interrupted - shutting down", component="BatchSyncHandler")
                    break
                
                # Fetch the next batch of unsynced records
                human_records, traffic_records = self._fetch_batch()
  
                # If no records were found, we're done
                total_records = len(human_records) + len(traffic_records)
                if total_records == 0:
                    break

                # Process this batch
                batch_num += 1
                total_processed += total_records

                self._sync_batch(human_records, traffic_records, batch_num)

                # Add a small delay between batches
                time.sleep(0.1)

            logger.info(
                "Sync cycle completed",
                context={
                    "batches_processed": batch_num,
                    "records_processed": total_processed
                },
                component="BatchSyncHandler"
            )

        except Exception as e:
            error_msg = "Error processing unsynced data"
            logger.error(
                error_msg,
                exception=e,
                component="BatchSyncHandler"
            )
            raise SyncError(
                error_msg,
                code="SYNC_PROCESS_FAILED",
                details={"error": str(e)},
                source="BatchSyncHandler"
            ) from e

 
    def _fetch_batch(self) -> Tuple[List[Dict], List[Dict]]:
        """Fetch a batch of unsynced records that are not currently being processed
        
        Returns:
            Tuple[List[Dict], List[Dict]]: Human and traffic records with their IDs

        Raises:
            DatabaseError: If a database operation fails
        """

        human_records = []
        traffic_records = []
        
        with self.db_manager.session_scope() as session:
            # Get unsynced human results that aren't being processed
            try:
                cutoff_time = datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(minutes=2)
                human_query = session.query(HumanResult).filter(
                    HumanResult.is_synced == False,
                    HumanResult.is_processing == False,
                    HumanResult.created_at < cutoff_time
                ).order_by(HumanResult.timestamp).limit(self.sync_batch_size)

                traffic_query = session.query(TrafficResult).filter(
                    TrafficResult.is_synced == False,
                    TrafficResult.is_processing == False,
                    TrafficResult.created_at < cutoff_time
                ).order_by(TrafficResult.timestamp).limit(self.sync_batch_size)

                # Mark these records as processing and collect them
                for record in human_query:
                    human_records.append(record.to_dict())
                    record.is_processing = True
                
                # Mark these records as processing and collect them
                for record in traffic_query:
                    traffic_records.append(record.to_dict())
                    record.is_processing = True

                return human_records, traffic_records
            except Exception as e:
                logger.error(
                    "Database error in  fetching batch of unsynced records",
                    exception=e,
                    component="BatchSyncHandler"
                )
                session.rollback()
                return [], []                     

    def _sync_batch(self, human_records: List[Dict], traffic_records: List[Dict], batch_num: int) -> None:
        """sync a batch of unsynched data
        
        Args:
            human_records: List of human result records
            traffic_records: List of traffic result records
            batch_num: Current batch number

        """
        try:
            total_records = len(human_records) + len(traffic_records)
            if total_records == 0:
                logger.debug(f"No records to sync in batch {batch_num}", component="BatchSyncHandler")
                return

            # Prepare the payload
            batch_id = f"{self.device_id}-{int(time.time())}-{batch_num}"
            payload = {
                "device_id": self.device_id,
                "batch_id": batch_id,
                "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
                "batch_num": batch_num,
                "record_count": total_records,
                "human_data": human_records,
                "traffic_data": traffic_records
            }
            
            # Track this batch for retries
            self.retry_count[batch_id] = 0

            # Send the data
            self._send_batch(batch_id, payload)
        
        except Exception as e:
            error_msg = f"Error preparing sync batch {batch_num}"
            logger.error(
                error_msg,
                exception=e,
                context={"batch_num": batch_num, "record_count": total_records},
                component="BatchSyncHandler"
            )
            if human_records or traffic_records:
                self._reset_processing_flags(human_records, traffic_records)


    def _send_batch(self, batch_id: str, payload: Dict[str, Any], is_retry:bool = False) -> None:
        """Send a batch of data to AWS IoT Core and schedule retry upon failure
        Args:
            batch_id: Unique identifier for this batch
            payload: Data payload to send
            is_retry: Whether this is a retry attempt
        
        """
        try:
            # Compress if enabled
            if self.compression_enabled:
                json_str = json.dumps(payload)
                compressed = gzip.compress(json_str.encode('utf-8'))
                encoded_payload = base64.b64encode(compressed).decode('utf-8')
                message = {
                    "compressed": True,
                    "data": encoded_payload
                }
            else:
                message = {
                    "compressed": False,
                    "data": payload
                }
            
            if hasattr(self.cloud_connector, 'connected_event') and not self.cloud_connector.connected_event.wait(timeout=5):
                logger.warning(
                    "Cloud connection not available, scheduling retry",
                    context={"batch_id": batch_id},
                    component="BatchSyncHandler"
                )
                self._schedule_retry(batch_id, payload)
                return 

            try:
                # Send to IoT Core
                success = self.cloud_connector.publish(self.sync_topic, json.dumps(message))
            except Exception as e:
                logger.error(
                    "Error publishing to cloud",
                    exception=e,
                    context={"batch_id": batch_id, "topic": self.sync_topic},
                    component="BatchSyncHandler"
                )               

            if success:
                logger.info(
                    "Successfully sent batch to cloud",
                    context={
                        "batch_id": batch_id,
                        "record_count": payload['record_count']
                    },
                    component="BatchSyncHandler"
                )

                # Mark records as synced
                self._mark_records_synced(payload)
                # Remove from retry tracking
                if batch_id in self.retry_count:
                    del self.retry_count[batch_id]
            else:
                logger.warning(
                    "Cloud publish returned false",
                    context={"batch_id": batch_id},
                    component="BatchSyncHandler"
                )
                self._schedule_retry(batch_id, payload)
        
        except Exception as e:
            logger.error(
                "Unexpected error sending batch",
                exception=e,
                context={"batch_id": batch_id, "is_retry": is_retry},
                component="BatchSyncHandler"
            )
            self._schedule_retry(batch_id, payload)

    def _mark_records_synced(self, payload: Dict[str, Any]):
        """Mark records as synced in the database
        
        Args:
            payload: The payload containing the records to mark as synced
        """
        with self.db_manager.session_scope() as session:
            try:
                # Mark human records as synced
                human_ids = [record["id"] for record in payload["human_data"]]
                if human_ids:
                    human_updated = session.query(HumanResult).filter(
                        HumanResult.id.in_(human_ids)
                    ).update({
                        "is_synced": True,
                        "is_processing": False
                    }, synchronize_session=False)


                # Mark traffic records as synced
                traffic_ids = [record["id"] for record in payload["traffic_data"]]
                if traffic_ids:
                    traffic_updated = session.query(TrafficResult).filter(
                        TrafficResult.id.in_(traffic_ids)
                    ).update({
                        "is_synced": True,
                        "is_processing": False
                    }, synchronize_session=False)
                
                # Commits happens automatically due to session_scope
            except Exception as e:
                logger.error(
                    "Database error while marking records as synced",
                    exception=e,
                    context={"error": str(e)},
                    component="BatchSyncHandler"
                )      
                session.rollback()
                human_records = payload.get("human_data", [])
                traffic_records = payload.get("traffic_data", [])
                self._reset_processing_flags(human_records, traffic_records)


    def _reset_processing_flags(self, human_records: List[Dict], traffic_records: List[Dict]):
        """Reset processing flags for records in case of errors
        
        Args:
            human_records: List of human result records
            traffic_records: List of traffic result records
        """
        with self.db_manager.session_scope() as session:
            try:
                # Reset processing flag for human records
                human_ids = [record["id"] for record in human_records]
                if human_ids:
                    human_updated = session.query(HumanResult).filter(
                        HumanResult.id.in_(human_ids)
                    ).update({
                        "is_processing": False
                    }, synchronize_session=False)

                # Mark traffic records as synced
                traffic_ids = [record["id"] for record in traffic_records]
                if traffic_ids:
                    traffic_updated = session.query(TrafficResult).filter(
                        TrafficResult.id.in_(traffic_ids)
                    ).update({
                        "is_processing": False
                    }, synchronize_session=False)

                # Commits happens automatically due to session_scope
            except Exception as e:
                logger.error(
                    "Error resetting processing flags",
                    exception=e,
                    component="BatchSyncHandler"
                )
                session.rollback()



    def _schedule_retry(self, batch_id: str, payload: Dict[str, Any]):
        """Schedule a retry with exponential backoff
        
        Args:
            batch_id: The batch ID to retry
            payload: The payload to send
        """
        if batch_id not in self.retry_count:
            self.retry_count[batch_id] = 0

        retry_count = self.retry_count[batch_id]
        if retry_count >= self.max_retries:
            logger.warning(
                "Exceeded max retries for batch",
                context={
                    "batch_id": batch_id,
                    "max_retries": self.max_retries
                },
                component="BatchSyncHandler"
            )
            # Reset processing flags since we've given up on this batch
            human_records = payload.get("human_data", [])
            traffic_records = payload.get("traffic_data", [])
            self._reset_processing_flags(human_records, traffic_records)
            # Remove from retry tracking
            if batch_id in self.retry_count:
                del self.retry_count[batch_id]
            return
        
        # Calculate backoff time with exponential backoff and some jitter to prevent thundering herd
        backoff_seconds = self.initial_backoff * (2 ** retry_count)
        jitter = backoff_seconds * 0.2 * (1 - 2 * random.random())
        backoff_seconds = max(1, backoff_seconds + jitter)

        logger.info(
            "Scheduling retry for batch",
            context={
                "batch_id": batch_id,
                "retry": retry_count + 1,
                "max_retries": self.max_retries,
                "backoff_seconds": round(backoff_seconds, 1)
            },
            component="BatchSyncHandler"
        )
        # Increment retry count
        self.retry_count[batch_id] += 1

        # Schedule retry using a time

        timer = threading.Timer(backoff_seconds, self._send_batch, args=[batch_id, payload, True])
        timer.daemon = True
        timer.start()

    @handle_errors(component="BatchSyncHandler")
    def cleanup_stale_processing(self, max_age_minutes: int = 60):
        """Reset processing flag for records that have been stuck in processing state
        
        Args:
            max_age_minutes: Maximum time (in minutes) a record can be in processing state
        """ 
        with self.db_manager.session_scope() as session:
            try:
                # Calculate the cutoff time
                cutoff_time = datetime.now(ZoneInfo("Asia/Tokyo")) - timedelta(minutes=max_age_minutes)
                # Reset human records
                human_count = session.query(HumanResult).filter(
                    HumanResult.is_processing == True,
                    HumanResult.is_synced == False,
                    HumanResult.last_updated < cutoff_time
                ).update({"is_processing": False})
                
                # Reset traffic records
                traffic_count = session.query(TrafficResult).filter(
                    TrafficResult.is_processing == True,
                    TrafficResult.is_synced == False,
                    TrafficResult.last_updated < cutoff_time
                ).update({"is_processing": False})
                
                total_reset = human_count + traffic_count
                if total_reset > 0:
                    logger.info(
                        f"Reset processing flag for stale records",
                        context={
                            "human_records": human_count,
                            "traffic_records": traffic_count,
                            "max_age_minutes": max_age_minutes
                        },
                        component="BatchSyncHandler"
                    )
        
            except Exception as e:
                logger.error(
                    "Error cleaning up stale processing records",
                    exception=e,
                    component="BatchSyncHandler"
                )
                session.rollback()

