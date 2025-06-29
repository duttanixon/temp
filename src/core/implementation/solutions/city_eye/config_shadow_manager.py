import json
import os
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from core.implementation.common.logger import get_logger
from .cloud_manager import CloudManager

logger = get_logger()

class ShadowConfigManager:
    def __init__(
        self,
        cloud_manager: CloudManager,
        config: Dict[str, Any], 
        xlines_config_path: str ):
    
        self.component_name = "ShadowConfigManager"
        self.connector = cloud_manager.cloud_connector
        self.xlines_config_path = xlines_config_path
        self.config = config

        self._config_update_callback = None

    
    def set_update_config_callback(self, callback: Callable):
        """Set callback for updating the configuration."""
        self._config_update_callback = callback
    

    def subscribe_to_delta(self):
        delta_topic = self.connector.shadow_delta_topic_template.format(thingName=self.connector.thing_name, shadowName=self.config.get("cloud", {}).get("config_shadow_name"))
        if delta_topic:
            logger.info(f"Subscribing to shadow delta topic: {delta_topic}", component=self.component_name)
            # The callback for AWSIoTCoreConnector.subscribe takes (topic, payload_str)
            # Assuming qos=1 for delta messages.
            self.connector.subscribe(delta_topic, self._handle_delta_message, qos=1)
        else:
            logger.error("Could not get shadow delta topic. Cannot subscribe", component= self.component_name)

    def _handle_delta_message(self, topic: str, payload_str: str):
        """
        This callback is executed by the MQTT thread and must return quickly.
        It offloads the actual processing to a worker thread.
        """
        logger.info(f"Received delta message on topic {topic}. Offloading to worker thread.", component=self.component_name)
        
        # Create and start a new thread to handle the processing.
        # This prevents blocking the MQTT client's thread.
        worker_thread = threading.Thread(
            target=self._process_delta_update_worker,
            args=(topic, payload_str)
        )
        worker_thread.daemon = True
        worker_thread.start()

    def _process_delta_update_worker(self, topic: str, payload_str: str):
        """
        This worker runs in a separate thread to process the delta update,
        preventing a deadlock on the MQTT callback thread.
        """
        logger.info(f"Processing delta update in a new thread.", component=self.component_name)
        try:
            delta_message = json.loads(payload_str)
            desired_state_node = delta_message.get("state", {})
            # desired_state_node = state_node.get("desired", {})
            message_id = desired_state_node.get("xlines_config_management", "Unknown").get("message_id","unknown")
            if "xlines_cfg_content" not in desired_state_node:
                logger.info("No 'xlines_cfg_content' key in delta state. Ignoring.", component=self.component_name)
                return
                
            version = desired_state_node.get("version", "")  # Shadow version
            new_xlines_content = desired_state_node["xlines_cfg_content"]

            if new_xlines_content is not None:
                logger.info("Delta contains new xlines_cfg_content.", component=self.component_name)
                try:
                    os.makedirs(os.path.dirname(self.xlines_config_path), exist_ok=True)
                    with open(self.xlines_config_path, 'w') as f:
                        if isinstance(new_xlines_content, (dict, list)):
                            json.dump(new_xlines_content, f, indent=4)
                        elif isinstance(new_xlines_content, str):
                            parsed_json = json.loads(new_xlines_content)
                            json.dump(parsed_json, f, indent=4)
                        else:
                            logger.error(f"Unsupported type for xlines_cfg_content: {type(new_xlines_content)}.", component=self.component_name)
                            self._update_reported_status("failed", message_id, version, error=f"Unsupported xlines_cfg_content type: {type(new_xlines_content)}")
                            return

                    logger.info(f"Successfully updated local xlines_cfg.json at {self.xlines_config_path}", component=self.component_name)

                    # Notify the application to reload the configuration
                    success = self._config_update_callback(self.xlines_config_path, new_xlines_content)
                    
                    if success:
                        # Update reported state - this blocking call is now safe
                        self._update_reported_status("successful", message_id, version, content=new_xlines_content)
                    else:
                        self._update_reported_status("failed", message_id, version, error="Application failed to reload config.")

                except Exception as e:
                    logger.error("Error processing and applying xlines delta", exception=e, component=self.component_name)
                    self._update_reported_status("failed", message_id, version, error=str(e))
        except Exception as e:
            logger.error("Fatal error in delta processing worker thread", exception=e, component=self.component_name)


    def _update_reported_status(self, status: str, message_id: Optional[str] = None, version: Optional[int] = None, details: Optional[str] = None, error: Optional[str] = None, content: Optional[str]=None):
        reported_payload = {
            "xlines_config_management": {
                "status": status,
                "last_update_timestamp": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()
            }
        }
        if message_id:
            reported_payload["xlines_config_management"]["message_id"] = message_id            
        if details:
            reported_payload["xlines_config_management"]["details"] = details
        if error:
            reported_payload["xlines_config_management"]["error"] = error
        if version:
            reported_payload["xlines_config_management"]["version"] = version
        if content is not None:
            reported_payload["xlines_cfg_content"] = content

        success = self._update_device_shadow_reported_state(reported_payload)

        if success:
            logger.info(f"Successfully reported xlines status: {status}", component=self.component_name)
            return True
        else:
            logger.error(f"Failed to report xlines status: {status}", component=self.component_name)
            return False


    def _update_device_shadow_reported_state(self, reported_state: Dict[str, Any], message_id: Optional[str] = None, qos: int = 1) -> bool:

        topic = self.connector.shadow_update_topic_template.format(thingName=self.connector.thing_name, shadowName=self.config.get("cloud", {}).get("config_shadow_name"))

        if not topic:
            return False # Should not happen if is_shadow_enabled is true

        desired_null_state = {key: None for key in reported_state.keys()}
        shadow_payload_dict = {"state": {"reported": reported_state, "desired": desired_null_state}}
        if message_id:
            shadow_payload_dict["message_id"] = message_id
        
        payload_str = json.dumps(shadow_payload_dict)
        return self.connector.publish(topic, payload_str, qos, is_shadow_update=True)


    def get_initial_config_from_shadow(self):
        """Optional: Fetch the current shadow state on startup."""
        shadow_name = self.config.get("cloud", {}).get("config_shadow_name")
        get_topic = self.connector.shadow_get_topic_template.format(thingName=self.connector.thing_name, shadowName=shadow_name)
        accepted_topic = self.connector.shadow_get_accepted_topic_template.format(thingName=self.connector.thing_name, shadowName=shadow_name)
        rejected_topic = self.connector.shadow_get_rejected_topic_template.format(thingName=self.connector.thing_name, shadowName=shadow_name)

        if not all([get_topic, accepted_topic, rejected_topic]):
            logger.error("Could not formulate all necessary shadow GET topics.", component=self.component_name)
            return

        # Temporary callback for /get/accepted
        def _handle_get_accepted(topic_str, payload_str_accepted):
            logger.info(f"Received current shadow state on {topic_str}", 
                        context={"payload_preview": payload_str_accepted[:200]}, component=self.component_name)
            try:
                shadow_doc = json.loads(payload_str_accepted)
                desired_state = shadow_doc.get("state", {}).get("desired", {})
                
                if "xlines_cfg_content" in desired_state and desired_state["xlines_cfg_content"] is not None:
                    logger.info("Initial 'desired.xlines_cfg_content' found in shadow. Processing as a delta.", component=self.component_name)
                    # Simulate a delta message to trigger the update logic
                    simulated_delta_payload = {
                        "state": desired_state, # Pass the whole desired state
                        "version": shadow_doc.get("version"),
                        "metadata": shadow_doc.get("metadata", {}).get("desired", {})
                    }
                    self._handle_delta_message(topic_str, json.dumps(simulated_delta_payload))
                else:
                    logger.info("No 'desired.xlines_cfg_content' or it's null in initial shadow state.", component=self.component_name)

            except Exception as e:
                logger.error("Error processing initial shadow GET response.", exception=e, component=self.component_name)
            finally:
                pass

        def _handle_get_rejected(topic_str, payload_str_rejected):
            try:
                payload = json.loads(payload_str_rejected)
                # Check if the rejection is because the shadow doesn't exist (404)
                if payload.get("code") == 404:
                    logger.warning(f"Shadow does not exist, as expected on first run. Payload: {payload_str_rejected}", component=self.component_name)
                    self._report_initial_state()
                else:
                    logger.error(f"Shadow GET request rejected on {topic_str}", 
                                context={"payload": payload_str_rejected}, component=self.component_name)
            except Exception as e:
                logger.error(f"Unexpected Error while parsing rejected payload: {payload_str_rejected}", component=self.component_name)
            finally:
                pass

        self.connector.subscribe(accepted_topic, _handle_get_accepted, qos=1)
        self.connector.subscribe(rejected_topic, _handle_get_rejected, qos=1)
        
        success = self.connector.publish(get_topic, "{}", qos=1, is_shadow_update=True) # Empty payload for GET
        if success:
            logger.info(f"Requested current shadow state from {get_topic}", component=self.component_name)
        else:
            logger.error(f"Failed to publish GET request to {get_topic}", component=self.component_name)
            # Unsubscribe if publish failed, as we won't get a response
            self.connector.unsubscribe(accepted_topic)
            self.connector.unsubscribe(rejected_topic)

    def _report_initial_state(self):
        """
        Kicks off a new thread to handle reporting the initial state.
        """
        worker_thread = threading.Thread(target=self._report_initial_state_worker)
        worker_thread.daemon = True
        worker_thread.start()

    def _report_initial_state_worker(self):
        """
        Worker thread to read the local config and report it to the shadow.
        This runs in a separate thread to avoid blocking the MQTT callback.
        """
        try:
            logger.info("No existing shadow found. Reporting initial state from local config file.", component=self.component_name)
            
            # 1. Read the local configuration file
            with open(self.xlines_config_path, 'r') as f:
                local_config_content = json.load(f)
            
            # 2. Build and publish the reported state (this call is now safe)
            success = self._update_reported_status(
                "created_from_local", 
                details=f"Initial state reported from {self.xlines_config_path}",  
                content=json.dumps(local_config_content)
            )

            if success:
                logger.info("Successfully created shadow and reported initial state.", component=self.component_name)
            else:
                logger.error("Failed to report initial shadow state.", component=self.component_name)

        except FileNotFoundError:
            logger.warning(f"Local config file not found at {self.xlines_config_path}. Reporting empty initial state.", component=self.component_name)
            local_config_content = []
            self._update_reported_status("created_from_local", details="Local config not found, reported empty state", content=json.dumps(local_config_content))
        except Exception as e:
            logger.error("Failed to report initial shadow state", exception=e, component=self.component_name)
            self._update_reported_status("failed", error=f"Failed to report initial state: {str(e)}")

