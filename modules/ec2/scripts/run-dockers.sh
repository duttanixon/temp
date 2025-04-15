#!/bin/bash 

# This scripts runs PostgreSQL container with persistent storage on EBS volume

# PostgreSQL version
PG_VERSION="14.10"

# PostgreSQL container
PG_CONTAINER_NAME="platform-postgresdb"
# Frontend container
FE_CONTAINER_NAME="platform-frontend-container"
# Backend container
BE_CONTAINER_NAME="platform-backend-container"

# Data directories (from EBS volume mount)
PG_DATA_DIR="/opt/data/postgres"
BE_DATA_DIR="/opt/data/app_docker"

# Ensure data directories exist and have right permissions
if [ ! -d "$PG_DATA_DIR" ]; then
    sudo mkdir -p "$PG_DATA_DIR"
    sudo chown -R 999:987 "$PG_DATA_DIR" # 999 is the postgres user in the container
fi

if [ ! -d "$BE_DATA_DIR" ]; then
    sudo mkdir -p "$BE_DATA_DIR"
    sudo chown -R 995:985 "$BE_DATA_DIR" # Assuming app_docker user has UID 1000
fi

# Stop and remove PostgreSQL container if it exists
if [ "$(docker ps -a --filter name=$PG_CONTAINER_NAME -q)" ]; then
    echo "Container $PG_CONTAINER_NAME already exists, stopping and removing..."
    docker stop $PG_CONTAINER_NAME
    docker rm $PG_CONTAINER_NAME
fi


# Stop and remove Frontend container if it exists
if [ "$(docker ps -a --filter name=$FE_CONTAINER_NAME -q)" ]; then
    echo "Container $FE_CONTAINER_NAME already exists, stopping and removing..."
    docker stop $FE_CONTAINER_NAME
    docker rm $FE_CONTAINER_NAME
fi

# Stop and remove Backend container if it exists
if [ "$(docker ps -a --filter name=$BE_CONTAINER_NAME -q)" ]; then
    echo "Container $BE_CONTAINER_NAME already exists, stopping and removing..."
    docker stop $BE_CONTAINER_NAME
    docker rm $BE_CONTAINER_NAME
fi

# Run PostgreSQL container
docker run -d \
    --name $PG_CONTAINER_NAME \
    --restart unless-stopped \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}" \
    -e POSTGRES_USER="${POSTGRES_USER:-postgres}" \
    -e POSTGRES_DB="${POSTGRES_DB:-platformdb-dev}" \
    -p 5432:5432 \
    -v "$PG_DATA_DIR:/var/lib/postgresql/data" \
    postgres:$PG_VERSION


# Run Frontend container
docker run -d \
    --name $FE_CONTAINER_NAME \
    --restart unless-stopped \
    -e NODE_ENV="${NODE_ENV}" \
    -e API_URL="${API_URL}" \
    -p 3000:3000 \
    platform-frontend:latest

# Run Backend container
docker run -d \
    --name $BE_CONTAINER_NAME \
    --restart unless-stopped \
    -e BACKEND_DEBUG="${BACKEND_DEBUG}" \
    -e API_KEY="${API_KEY}" \
    -e POSTGRES_USER="${POSTGRES_USER}" \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
    -e POSTGRES_DB="${POSTGRES_DB}" \
    -p 8000:80 \
    -v "$BE_DATA_DIR:/data" \
    --user app_docker \
    platform-backend:latest