#!/bin/bash

# PostgreSQL container
PG_CONTAINER_NAME="platform-postgresdb"
# Frontend container
FE_CONTAINER_NAME="platform-frontend-container"
# Backend container
BE_CONTAINER_NAME="platform-backend-container"

# Stop PostgreSQL container
if [ "$(docker ps -q -f name=$PG_CONTAINER_NAME)" ]; then
    echo "Stopping $PG_CONTAINER_NAME container..."
    docker stop $PG_CONTAINER_NAME
fi

# Stop Frontend container
if [ "$(docker ps -q -f name=$FE_CONTAINER_NAME)" ]; then
    echo "Stopping $FE_CONTAINER_NAME container..."
    docker stop $FE_CONTAINER_NAME
fi

# Stop Backend container
if [ "$(docker ps -q -f name=$BE_CONTAINER_NAME)" ]; then
    echo "Stopping $BE_CONTAINER_NAME container..."
    docker stop $BE_CONTAINER_NAME
fi

echo "All containers stopped!"