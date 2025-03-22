#!/bin/bash

# Start all Docker Compose services
start_services() {
    echo "Starting services..."

    # Start mlflow
    cd ./mlflow
    docker compose up -d --build
    cd ..

    # Start airflow
    cd ./airflow
    docker compose up -d --build
    cd ..

    # Start jenkins
    cd ./jenkins
    docker compose up -d --build
    cd ..

    # Start monitoring
    cd ./monitor
    docker compose up -d --build
    cd ..

    # Start psql
    cd ./psql_img
    docker compose up -d --build
    cd ..

    # Start Kafka
    cd ./kafka
    docker compose up -d --build
    cd ..

    echo "All services have been started."
}

# Stop all Docker Compose services
stop_services() {
    echo "Shutting down services..."

    # Stop airflow
    cd ./airflow
    docker compose down
    cd ..

    # Stop mlflow
    cd ./mlflow
    docker compose down
    cd ..

    # Stop jenkins
    cd ./jenkins
    docker compose down
    cd ..

    # Stop monitoring
    cd ./monitor
    docker compose down
    cd ..

    # Stop psql
    cd ./psql_img
    docker compose down
    cd ..

    # Stop Kafka
    cd ./kafka
    docker compose down
    cd ..

    echo "All services have been shut down."
}

# Check the argument to decide whether to start or stop services
if [ "$1" == "start" ]; then
    start_services
elif [ "$1" == "stop" ]; then
    stop_services
else
    echo "Usage: $0 {start|stop}"
    exit 1
fi