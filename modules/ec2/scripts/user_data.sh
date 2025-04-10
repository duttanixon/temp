#!/bin/bash
set -e

# Install necessary packages for Ubuntu
sudo apt-get update
sudo apt-get install -y curl unzip ca-certificates

# # Install AWS CLI
# echo "Installing AWS CLI..."
# curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
# unzip awscliv2.zip
# ./aws/install
# rm -rf aws awscliv2.zip  # Clean up temporary files

# install jq git
# sudo apt install -y postgresql-all
sudo apt install -y git-all jq


# install docker
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker post-installation
echo "Configuring Docker permissions..."
sudo groupadd -f docker  # -f prevents errors if group already exists
sudo usermod -aG docker ubuntu  # Explicitly name the ubuntu user
sudo systemctl enable docker
newgrp docker

# Mount EBS volume
echo "Mounting data volume..."
DATA_DEVICE="/dev/nvme1n1"
DATA_DIR="/opt/data"
mkdir -p $DATA_DIR

# Wait for device to become available
max_retries=10
retry_count=0
while [ ! -e $DATA_DEVICE ] && [ $retry_count -lt $max_retries ]; do
  echo "Waiting for device $DATA_DEVICE to become available... ($retry_count/$max_retries)"
  sleep 5
  retry_count=$((retry_count+1))
done

if [ ! -e $DATA_DEVICE ]; then
  echo "ERROR: Device $DATA_DEVICE did not become available after $max_retries retries"
  exit 1
fi

# Check if the volume is already formatted
if [ "$(file -s $DATA_DEVICE)" = "$DATA_DEVICE: data" ]; then
  echo "Formatting data volume..."
  mkfs -t xfs $DATA_DEVICE
  # Wait for formatting to complete
  sleep 5
fi

# Add to fstab for automatic mounting on reboot
if ! grep -q "$DATA_DEVICE" /etc/fstab; then
  echo "$DATA_DEVICE $DATA_DIR xfs defaults,nofail 0 2" >> /etc/fstab
fi

# Mount with retry
retry_count=0
while ! mount -a && [ $retry_count -lt $max_retries ]; do
  echo "Retrying mount... ($retry_count/$max_retries)"
  sleep 5
  retry_count=$((retry_count+1))
done

# Verify mount was successful
if ! mountpoint -q $DATA_DIR; then
  echo "ERROR: Failed to mount $DATA_DEVICE to $DATA_DIR"
  exit 1
fi

echo "EBS volume successfully mounted at $DATA_DIR"

# Create directory structure
mkdir -p $DATA_DIR/postgres
mkdir -p $DATA_DIR/keycloak
mkdir -p $DATA_DIR/app/frontend
mkdir -p $DATA_DIR/app/backend
mkdir -p $DATA_DIR/nginx

# Set correct permissions
chown -R postgres:postgres $DATA_DIR/postgres
chown -R ubuntu:ubuntu $DATA_DIR/keycloak
chown -R ubuntu:ubuntu $DATA_DIR/app
chown -R ubuntu:ubuntu $DATA_DIR/nginx


# Add engineer SSH keys
mkdir -p /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh
touch /home/ubuntu/.ssh/authorized_keys
chmod 600 /home/ubuntu/.ssh/authorized_keys
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
