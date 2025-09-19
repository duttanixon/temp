#!/usr/bin/env python3
"""
Device Provisioner - Creates directories, detects MAC address, and downloads certificates
"""

import os
import glob
import requests
from urllib.parse import urlparse, unquote
import json
import sys
import subprocess
import re
import time
from pathlib import Path


class DeviceProvisioner:
    def __init__(self):
        self.base_dirs = [
            "/home/cybercore/application",
            "/home/cybercore/certificates", 
            "/home/cybercore/configs",
            "/home/cybercore/db",
            "/home/cybercore/models",
            "/var/log/edge-analytics"
        ]
        self.certificates_dir = "/home/cybercore/certificates"
        self.api_url = "https://platform.cybercore.co.jp/api/v2/devices/certificates-for-devices"
        self.api_key = "k-TzDzlJew9s3Z_NXJprY4cwgL0IeiaQeZ8fHVx2N8M"
        self.amazon_root_ca_url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"

    def create_directories(self):
        """Create all necessary directories if they don't exist"""
        print("Creating directories...")
        for directory in self.base_dirs:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                print(f"✓ Directory created/verified: {directory}")
            except PermissionError:
                print(f"✗ Permission denied creating directory: {directory}")
                return False
            except Exception as e:
                print(f"✗ Error creating directory {directory}: {e}")
                return False
        
        # Set ownership of all directories to cybercore:cybercore
        print("Setting directory ownership...")
        for directory in self.base_dirs:
            try:
                subprocess.run(['chown', '-R', 'cybercore:cybercore', directory], 
                             check=True, capture_output=True, text=True)
                print(f"✓ Ownership set to cybercore:cybercore for: {directory}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to set ownership for {directory}: {e}")
                return False
            except Exception as e:
                print(f"✗ Error setting ownership for {directory}: {e}")
                return False
        
        return True

    def get_mac_address(self):
        """Get MAC address from /sys/class/net/ interface"""
        print("Detecting MAC address...")
        
        # Check if /sys/class/net/ exists
        net_path = "/sys/class/net/"
        if not os.path.exists(net_path):
            print(f"✗ Network interface path {net_path} not found")
            return None

        try:
            # List all network interfaces
            interfaces = os.listdir(net_path)
            print(f"Available interfaces: {interfaces}")
            
            # Define interface priority order
            interface_priorities = [
                ('enp', 'ethernet (enp series)'),
                ('eth', 'ethernet (eth series)'),
                ('wlan', 'wireless (wlan series)')
            ]
            
            # Try interfaces in priority order
            for prefix, description in interface_priorities:
                matching_interfaces = sorted([iface for iface in interfaces if iface.startswith(prefix)])
                if matching_interfaces:
                    print(f"Found {description} interfaces: {matching_interfaces}")
                    for interface in matching_interfaces:
                        mac_address = self._read_mac_from_interface(interface)
                        if mac_address:
                            print(f"✓ MAC address found from {interface}: {mac_address}")
                            return mac_address
            
            print("✗ No suitable network interface found (searched for enp*, eth*, wlan*)")
            return None
            
        except Exception as e:
            print(f"✗ Error reading network interfaces: {e}")
            return None

    def _read_mac_from_interface(self, interface):
        """Read MAC address from a specific interface"""
        try:
            address_file = f"/sys/class/net/{interface}/address"
            if os.path.exists(address_file):
                with open(address_file, 'r') as f:
                    mac_address = f.read().strip()
                    # Validate MAC address format (basic check)
                    if len(mac_address) == 17 and mac_address.count(':') == 5:
                        return mac_address
        except Exception as e:
            print(f"Warning: Could not read MAC from {interface}: {e}")
        return None

    def check_certificates_exist(self):
        """Check if .pem and .key files exist in certificates directory"""
        print("Checking for existing certificates...")
        
        pem_files = glob.glob(os.path.join(self.certificates_dir, "*.pem"))
        key_files = glob.glob(os.path.join(self.certificates_dir, "*.key"))
        
        if pem_files and key_files:
            print(f"✓ Certificates found: {len(pem_files)} .pem files, {len(key_files)} .key files")
            return True
        else:
            print(f"✗ Certificates missing: {len(pem_files)} .pem files, {len(key_files)} .key files")
            return False

    def download_certificates(self, mac_address):
        """Download certificates using the API"""
        print(f"Downloading certificates for MAC address: {mac_address}")
        
        # URL encode the MAC address (only encode colons as %3A)
        encoded_mac = mac_address.replace(':', '%3A')
        url = f"{self.api_url}?device_identifier={encoded_mac}"
        
        headers = {
            'x-api-key': self.api_key
        }
        
        try:
            # Make API request
            print(f"Making API request to: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print("✓ API response received")
            
            # Extract URLs
            certificate_url = data.get('certificate_url')
            private_key_url = data.get('private_key_url')
            device_id = data.get('device_id')
            
            if not certificate_url or not private_key_url:
                print("✗ Certificate or private key URL not found in response")
                return False
            
            # Extract original filenames from URLs
            cert_filename = self._extract_filename_from_url(certificate_url, "certificate.pem")
            cert_path = os.path.join(self.certificates_dir, cert_filename)
            
            print(f"Downloading certificate to: {cert_path}")
            if self._download_file(certificate_url, cert_path):
                print("✓ Certificate downloaded successfully")
            else:
                return False
            
            # Download private key file
            key_filename = self._extract_filename_from_url(private_key_url, "private.key")
            key_path = os.path.join(self.certificates_dir, key_filename)
            
            print(f"Downloading private key to: {key_path}")
            if self._download_file(private_key_url, key_path):
                print("✓ Private key downloaded successfully")
            else:
                return False
            
            print("✓ All certificates downloaded successfully")
            print(f"Device ID: {device_id}")
            print(f"MAC Address: {data.get('mac_address')}")
            print(f"Expires at: {data.get('expires_at')}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ API request failed: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse API response: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during certificate download: {e}")
            return False

    def _extract_filename_from_url(self, url, fallback_name):
        """Extract the original filename from a URL"""
        try:
            # Parse the URL and extract the path
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            
            # Get the filename from the path
            filename = os.path.basename(path)
            
            # If filename is empty or doesn't have an extension, use fallback
            if not filename or '.' not in filename:
                return fallback_name
            
            return filename
            
        except Exception as e:
            print(f"Warning: Could not extract filename from URL: {e}")
            return fallback_name

    def _download_file(self, url, filepath):
        """Download a file from URL to filepath"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to download file: {e}")
            return False

    def set_permissions(self):
        """Set proper permissions for certificates directory and files"""
        print("Setting file permissions...")
        try:
            # Set certificates directory permission to 700 (drwx------)
            os.chmod(self.certificates_dir, 0o700)
            print(f"✓ Set directory permission 700 for: {self.certificates_dir}")
            
            # Set .key files to 600 (private key files should be private)
            key_files = glob.glob(os.path.join(self.certificates_dir, "*.key"))
            for key_file in key_files:
                os.chmod(key_file, 0o600)
                print(f"✓ Set permission 600 for key file: {key_file}")
            
            # Set .pem files to 644 (certificate files can be readable)
            pem_files = glob.glob(os.path.join(self.certificates_dir, "*.pem"))
            for pem_file in pem_files:
                os.chmod(pem_file, 0o644)
                print(f"✓ Set permission 644 for certificate file: {pem_file}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error setting permissions: {e}")
            return False

    def download_amazon_root_ca(self):
        """Download Amazon Root CA certificate"""
        print("Downloading Amazon Root CA certificate...")
        
        amazon_ca_path = os.path.join(self.certificates_dir, "AmazonRootCA1.pem")
        
        # Check if it already exists
        if os.path.exists(amazon_ca_path):
            print(f"✓ Amazon Root CA already exists: {amazon_ca_path}")
            return True
        
        try:
            print(f"Downloading from: {self.amazon_root_ca_url}")
            response = requests.get(self.amazon_root_ca_url, timeout=30)
            response.raise_for_status()
            
            with open(amazon_ca_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Amazon Root CA downloaded: {amazon_ca_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to download Amazon Root CA: {e}")
            return False

    def extract_hostname_from_certificate(self):
        """Extract hostname from certificate filename"""
        print("Extracting hostname from certificate...")
        
        # Look for .pem files that are not AmazonRootCA1.pem
        pem_files = [f for f in glob.glob(os.path.join(self.certificates_dir, "*.pem")) 
                     if not f.endswith("AmazonRootCA1.pem")]
        
        if not pem_files:
            print("✗ No device certificate files found")
            return None
        
        # Take the first device certificate file
        cert_file = pem_files[0]
        cert_filename = os.path.basename(cert_file)
        
        # Extract hostname using regex: look for pattern _HOSTNAME.pem
        # Example: f73ca19514be1c086a317ec540162563b23519e79f82362d320908850d182464_D-T6DSPR.pem
        match = re.search(r'_([A-Za-z0-9\-]+)\.pem$', cert_filename)
        
        if match:
            hostname = match.group(1)
            print(f"✓ Hostname extracted from certificate: {hostname}")
            return hostname
        else:
            print(f"✗ Could not extract hostname from certificate filename: {cert_filename}")
            return None

    def get_current_hostname(self):
        """Get current system hostname"""
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, check=True)
            current_hostname = result.stdout.strip()
            print(f"Current system hostname: {current_hostname}")
            return current_hostname
        except Exception as e:
            print(f"✗ Error getting current hostname: {e}")
            return None

    def update_hostname(self, new_hostname):
        """Update system hostname in /etc/hostname and /etc/hosts"""
        print(f"Updating system hostname to: {new_hostname}")
        
        try:
            # Update /etc/hostname
            print("Updating /etc/hostname...")
            with open('/etc/hostname', 'w') as f:
                f.write(f"{new_hostname}\n")
            print("✓ /etc/hostname updated")
            
            # Update /etc/hosts
            print("Updating /etc/hosts...")
            hosts_content = []
            hostname_updated = False
            
            if os.path.exists('/etc/hosts'):
                with open('/etc/hosts', 'r') as f:
                    for line in f:
                        if line.startswith('127.0.1.1'):
                            # Update the localhost entry
                            hosts_content.append(f"127.0.1.1\t{new_hostname}\n")
                            hostname_updated = True
                        else:
                            hosts_content.append(line)
            
            # If no 127.0.1.1 entry was found, add one
            if not hostname_updated:
                hosts_content.append(f"127.0.1.1\t{new_hostname}\n")
            
            with open('/etc/hosts', 'w') as f:
                f.writelines(hosts_content)
            print("✓ /etc/hosts updated")
            
            # Reboot to apply hostname changes completely
            print("Hostname files updated. Rebooting system to apply changes...")
            print("System will reboot in 5 seconds...")
            
            # Give user a moment to see the message
            time.sleep(5)
            
            # Reboot the system
            subprocess.run(['reboot'], check=True)
            
            # This line will not be reached due to reboot
            return True
            
        except Exception as e:
            print(f"✗ Error updating hostname: {e}")
            return False

    def check_and_update_hostname(self):
        """Check if hostname matches certificate and update if needed"""
        print("Checking hostname compatibility...")
        
        # Extract hostname from certificate
        cert_hostname = self.extract_hostname_from_certificate()
        if not cert_hostname:
            print("✗ Cannot proceed without certificate hostname")
            return False
        
        # Get current system hostname
        current_hostname = self.get_current_hostname()
        if not current_hostname:
            print("✗ Cannot get current hostname")
            return False
        
        # Compare hostnames
        if current_hostname == cert_hostname:
            print(f"✓ Hostname matches certificate: {current_hostname}")
            return True
        else:
            print(f"✗ Hostname mismatch - Current: {current_hostname}, Certificate: {cert_hostname}")
            return self.update_hostname(cert_hostname)

    def create_config_file(self):
        """Create or update /etc/dc-configs/config.json file"""
        print("Checking/creating device configuration file...")
        
        config_dir = "/etc/dc-configs"
        config_file = os.path.join(config_dir, "config.json")
        
        # Extract hostname from certificate for thing-name
        cert_hostname = self.extract_hostname_from_certificate()
        if not cert_hostname:
            print("✗ Cannot create config without certificate hostname")
            return False
        
        # Find certificate and key files
        pem_files = [f for f in glob.glob(os.path.join(self.certificates_dir, "*.pem")) 
                     if not f.endswith("AmazonRootCA1.pem")]
        key_files = glob.glob(os.path.join(self.certificates_dir, "*.key"))
        
        if not pem_files or not key_files:
            print("✗ Certificate or key files not found")
            return False
        
        cert_path = pem_files[0]  # Use first device certificate
        key_path = key_files[0]   # Use first key file
        root_ca_path = os.path.join(self.certificates_dir, "AmazonRootCA1.pem")
        
        # Create the configuration
        config = {
            "endpoint": "a23bd20ty64577-ats.iot.ap-northeast-1.amazonaws.com",
            "cert": cert_path,
            "key": key_path,
            "root-ca": root_ca_path,
            "thing-name": cert_hostname,
            "logging": {
                "enable-sdk-logging": True,
                "level": "DEBUG",
                "type": "STDOUT",
                "file": ""
            },
            "jobs": {
                "enabled": True,
                "handler-directory": ""
            },
            "tunneling": {
                "enabled": False
            },
            "device-defender": {
                "enabled": False,
                "interval": 300
            },
            "fleet-provisioning": {
                "enabled": False,
                "template-name": "",
                "template-parameters": "",
                "csr-file": "",
                "device-key": ""
            },
            "samples": {
                "pub-sub": {
                    "enabled": False,
                    "publish-topic": "",
                    "publish-file": "",
                    "subscribe-topic": "",
                    "subscribe-file": ""
                }
            },
            "config-shadow": {
                "enabled": False
            },
            "sample-shadow": {
                "enabled": False,
                "shadow-name": "",
                "shadow-input-file": "",
                "shadow-output-file": ""
            }
        }
        
        try:
            # Create config directory if it doesn't exist
            Path(config_dir).mkdir(parents=True, exist_ok=True)
            print(f"✓ Config directory created/verified: {config_dir}")
            
            # Check if config file exists and validate it
            if os.path.exists(config_file):
                print(f"Config file exists: {config_file}")
                if self._validate_config_file(config_file, config):
                    print("✓ Existing config file is correct")
                    return True
                else:
                    print("✗ Existing config file is incorrect, recreating...")
            
            # Write the config file
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ Config file created: {config_file}")
            print(f"✓ Thing name set to: {cert_hostname}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error creating config file: {e}")
            return False

    def _validate_config_file(self, config_file, expected_config):
        """Validate existing config file against expected configuration"""
        try:
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
            
            # Check critical fields
            critical_fields = ['endpoint', 'cert', 'key', 'root-ca', 'thing-name']
            
            for field in critical_fields:
                if existing_config.get(field) != expected_config.get(field):
                    print(f"Config mismatch in field '{field}': expected '{expected_config.get(field)}', got '{existing_config.get(field)}'")
                    return False
            
            return True
            
        except Exception as e:
            print(f"Error validating config file: {e}")
            return False

    def run(self):
        """Main execution flow"""
        print("=== Device Provisioner Starting ===")
        
        # Step 1: Create directories
        if not self.create_directories():
            print("✗ Failed to create directories. Exiting.")
            return False
        
        # Step 2: Check if certificates already exist
        certificates_exist = self.check_certificates_exist()
        
        if not certificates_exist:
            # Step 3: Get MAC address
            mac_address = self.get_mac_address()
            if not mac_address:
                print("✗ Could not detect MAC address. Exiting.")
                return False
            
            # Step 4: Download certificates
            if not self.download_certificates(mac_address):
                print("✗ Failed to download certificates. Exiting.")
                return False
        else:
            print("✓ Device certificates already exist. Skipping device certificate download.")
        
        # Step 5: Download Amazon Root CA certificate (always check/download)
        if not self.download_amazon_root_ca():
            print("✗ Failed to download Amazon Root CA certificate. Exiting.")
            return False
        
        # Step 6: Set file permissions (always set proper permissions)
        if not self.set_permissions():
            print("✗ Failed to set file permissions. Exiting.")
            return False
        
        # Step 7: Check and update hostname if needed
        if not self.check_and_update_hostname():
            print("✗ Failed to check/update hostname. Exiting.")
            return False
        
        # Step 8: Create or update device configuration file
        if not self.create_config_file():
            print("✗ Failed to create/update configuration file. Exiting.")
            return False
        
        print("=== Device Provisioner Completed Successfully ===")
        return True


def main():
    """Main entry point"""
    provisioner = DeviceProvisioner()
    success = provisioner.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
