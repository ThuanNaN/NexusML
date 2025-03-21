#!/bin/bash

# Function to start (up) a specific service
up_service() {
    local service=$1
    echo "Starting $service..."
    cd ./$service || { echo "Service $service not found!"; exit 1; }
    docker compose up -d --build
    cd - >/dev/null
}

# Function to stop (down) a specific service
down_service() {
    local service=$1
    echo "Stopping $service..."
    cd ./$service || { echo "Service $service not found!"; exit 1; }
    docker compose down
    cd - >/dev/null
}

# Function to start (up) all services
up_all() {
    for service in mlflow airflow jenkins monitor; do
        up_service $service
    done
    echo "All services have been started."
}

# Function to stop (down) all services
down_all() {
    for service in airflow mlflow jenkins monitor; do
        down_service $service
    done
    echo "All services have been shut down."
}

# Check command-line arguments
if [ "$1" == "up" ]; then
    if [ "$2" == "all" ]; then
        up_all
    elif [ -n "$2" ]; then
        up_service "$2"
    else
        echo "Usage: $0 up {service_name|all}"
        exit 1
    fi
elif [ "$1" == "down" ]; then
    if [ "$2" == "all" ]; then
        down_all
    elif [ -n "$2" ]; then
        down_service "$2"
    else
        echo "Usage: $0 down {service_name|all}"
        exit 1
    fi
else
    echo "Usage: $0 {up|down} {service_name|all}"
    exit 1
fi