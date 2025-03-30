import time
import json
import gzip
import base64
import random
import traceback
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

from core.implementation.common.sqlite_manager import DatabaseManager
from core.interfaces.cloud.cloud_connector import ICloudConnector
from .models import HumanResult, TrafficResult


class BatchSyncHandler:
    def __init__(self, db_manager: DatabaseManager, cloud_connector:ICloudConnector, config: Dict[str, Any]):
        """
        Initialize the batch synchonization handler
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
            print("Sync Handler is already running")
            return
        
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_worker)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        print(f"BatchHandler started with {self.sync_batch_size} batch size and {self.sync_interval}s interval")

    def stop(self):
        """Stop the sync handler thread"""
        self.running = False

    
    def _sync_worker(self):
        """Background worker that periodically synchonizes data"""
        while self.running:
            try:
                # Check if it's time to sync
                now = datetime.now(ZoneInfo("Asia/Tokyo"))
                time_since_last_sync = (now - self.last_sync_time).total_seconds()

                if time_since_last_sync >= self.sync_interval:
                    # Process all unsynced data in batches
                    self._process_all_unsynced_data()
                    self.last_sync_time = now

                # sleep a bit to avoiud high cpu usage                
                time.sleep(2)
            
            except Exception as e:
                print(f"Error in sync worker: {str(e)}")
                time.sleep(5)
    

    def _process_all_unsynced_data(self):
        """Process all unsynced data in batches"""
        try:
            # First, count total unsynced records
            with self.db_manager.session_scope() as session:
                total_human = session.query(HumanResult).filter_by(is_synced=False).count()
                total_traffic = session.query(TrafficResult).filter_by(is_synced=False).count()
            
            if total_human == 0 and total_traffic == 0:
                print("No records to sync")
                return
            
            # Calculate number of batches needed
            human_batches = (total_human + self.sync_batch_size -1) // self.sync_batch_size if total_human > 0 else 0
            traffic_batches = (total_traffic + self.sync_batch_size -1) // self.sync_batch_size if total_traffic > 0 else 0
            total_batches = max(human_batches, traffic_batches)

            print(f"Starting sync of {total_human} human records and {total_traffic} traffic records in {total_batches} batches")

            # process each batch
            for batch_num in range(total_batches):
                if not self.running:
                    print("Sync interrupted - shutting down")
                    break
                
                # Calculate offsets for this batch
                offset = batch_num * self.sync_batch_size

                # Process batch
                self._sync_batch(offset, batch_num + 1, total_batches)

                # Add a small delay between batches
                if batch_num < total_batches - 1:
                    time.sleep(0.1)
            
            print(f"Sync cycle completed: processed {total_batches} batches")

        except Exception as e:
            print(f"Error processing unsynced data: {str(e)}")


    def _sync_batch(self, offset: int, current_batch: int, total_batches: int):
        """Fetch and sync a batch of unsynched data"""
        try:
            human_records = []
            traffic_records = []

            with self.db_manager.session_scope() as session:
                # Get unsynced human results with offset
                human_query = session.query(HumanResult).filter_by(is_synced=False).order_by(
                    HumanResult.timestamp).offset(offset).limit(self.sync_batch_size)
                for record in human_query:
                    human_records.append(record.to_dict())

                # Get unsynced traffic results with offset
                traffic_query = session.query(TrafficResult).filter_by(is_synced=False).order_by(
                    TrafficResult.timestamp).offset(offset).limit(self.sync_batch_size)
                for record in traffic_query:
                    traffic_records.append(record.to_dict())
            
            total_records = len(human_records) + len(traffic_records)
            if total_records == 0:
                print(f"No records to sync in batch {current_batch}/{total_batches}")
                return

            # Prepare the payload
            batch_id = f"{self.device_id}-{int(time.time())}-{current_batch}"
            payload = {
                "device_id": self.device_id,
                "batch_id": batch_id,
                "timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
                "batch_info": {
                    "current": current_batch,
                    "total": total_batches
                },
                "record_count": total_records,
                "human_data": human_records,
                "traffic_data": traffic_records
            }
            
            # Track this batch for retries
            self.retry_count[batch_id] = 0

            # Send the data
            self._send_batch(batch_id, payload)
        
        except Exception as e:
            print(f"Error syncing batch: {str(e)}")


    def _send_batch(self, batch_id: str, payload: Dict[str, Any], is_retry:bool = False):
        """Send a batch of data to AWS IoT Core"""
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
                print(f"Not connected to AWS IoT Core, scheduling retry for batch {batch_id}")
                self._schedule_retry(batch_id, payload)
                return 

            # Send to IoT Core
            success = self.cloud_connector.publish(self.sync_topic, json.dumps(message))

            if success:
                batch_info = payload.get("batch_info", {})
                current = batch_info.get("current", "?")
                total = batch_info.get("total", "?")
                print(f"Successfully sent batch {current}/{total} (ID: {batch_id}) with {payload['record_count']} records")

                # Mark records as synced
                self._mark_records_synced(payload)
                # Remove from retry tracking
                if batch_id in self.retry_count:
                    del self.retry_count[batch_id]
            else:
                print(f"Failed to send batch {batch_id}")
                self._schedule_retry(batch_id, payload)
        
        except Exception as e:
            print(f"Error sending batch {batch_id}: {str(e)}")
            print(traceback.format_exc())
            self._schedule_retry(batch_id, payload)

    def _mark_records_synced(self, payload: Dict[str, Any]):
        """Mark records as synched in the database"""
        try:
            with self.db_manager.session_scope() as session:
                # Mark human records as synced
                for record in payload["human_data"]:
                    session.query(HumanResult).filter_by(id=record["id"]).update({"is_synced": True})
                
                # Mark traffic records as synced
                for record in payload["traffic_data"]:
                    session.query(TrafficResult).filter_by(id=record["id"]).update({"is_synced": True})
                
                # Commits happens automatically due to session_scope
        except Exception as e:
            print(f"Error marking records as synced: {str(e)}")


    def _schedule_retry(self, batch_id: str, payload: Dict[str, Any]):
        """Schedule a retry with exponential backoff"""
        if batch_id not in self.retry_count:
            self.retry_count[batch_id] = 0

        retry_count = self.retry_count[batch_id]
        if retry_count >= self.max_retries:
            print(f"Exceeded max retries ({self.max_retries}) for batch {batch_id}")
            return
        
        # Calculate backoff time with exponential backoff and some jitter to prevent thundering herd
        backoff_seconds = self.initial_backoff * (2 ** retry_count)
        jitter = backoff_seconds * 0.2 * (1 - 2 * random.random())
        backoff_seconds = max(1, backoff_seconds + jitter)

        print(f"Scheduling retry {retry_count + 1}/{self.max_retries} for batch {batch_id} in {backoff_seconds:.1f}s")

        # Increment retry count
        self.retry_count[batch_id] += 1

        # Schedule retry using a time

        timer = threading.Timer(backoff_seconds, self._send_batch, args=[batch_id, payload, True])
        timer.daemon = True
        timer.start()


    def force_sync(self):
        """Force an immediate synchronization"""
        print("Force sync requested")
        self.last_sync_time = datetime.min  # Set to past time to trigger immediate sync



