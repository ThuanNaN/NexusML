# Kafka Data Streaming

## Overview

Kafka Data Streaming is a project that automates the process of collecting, processing, and storing image data. It crawls images from [freeimages.com](freeimages.com), streams them through Apache Kafka, preprocesses the data, builds a dataset, and stores it in a PostgreSQL database managed via pgAdmin. This project is designed for developers and data engineers interested in real-time data pipelines and image dataset creation.
This project aims to provide a generalized MLOps solution that supports ML project, specifically project: **VAE-Based Image Colorization** where final dataset contain grayscale image and clean color image.

## Key Features

- **Data Crawler**: Scrapes images from [freeimages.com](https://www.freeimages.com) using Python and BeautifulSoup, with multithreading and polite delays for efficient, safe downloads.
- **Kafka Streaming**: Powers real-time image data flow with Apache Kafka, ensuring speed and reliability.

- **Image Processing**: Validates, resizes, and grayscales images, preparing them for storage via a consumer pipeline.

- **PostgreSQL Storage**: Stores processed datasets in PostgreSQL (via pgAdmin) for easy access in ML projects like **VAE-Based Image Colorization**.

## Tech Stack

- **Producer**:

  - Python 3.9+ with BeautifulSoup for web scraping
  - Multithreading for optimized image downloads
  - Kafka-Python for message production to Kafka topics

- **Streaming**:

  - Apache Kafka (with ZooKeeper) hosted via Docker for containerized deployment and simplified management

- **Consumer**:

  - Python with PIL for image preprocessing (resizing, grayscale conversion)
  - Kafka-Python for consuming messages
  - psycopg2 for PostgreSQL database connectivity

- **Database**:
  - PostgreSQL, managed via pgAdmin, for robust data storage and retrieval

## Getting Started

### 1. Clone repository

```bash
git clone +link_repo
```

```bash
cd data_pipeline
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Running Kafka with Docker

Build container from docker file

```bash
docker-compose up -d
docker ps
```

Enter Kafka container

```bash
docker exec -it kafka /bin/bash
```

Maker sure it turn on container cmd: `[appuser@f8d588076eb7 ~]$`  
Create kafka topic

```bash
kafka-topics --create --topic image-raw-data --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

verify topic was created

```bash
kafka-topics --list --bootstrap-server localhost:9092
```

If everything is ok, exit

```bash
exit
```

### 4. Exec PostgreSQL via `psql`

```python
psql -h localhost -U postgres -d image_db -p 5454
```

### 5. Running Python Code

Before running code, make sure you set the `PYTHONPATH` to `data_pipeline`, `data_pipeline/crawler`

First, running code consumer to wait message from kafka

```bash
python -m consumer.main
```

Then, let's run crawler code

```bash
python -m crawler.main
```
