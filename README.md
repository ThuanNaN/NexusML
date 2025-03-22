# NexusML – A Simple MLOps Framework

## Overview

NexusML is a highly modular and scalable MLOps framework designed to integrate deep learning models seamlessly into end-to-end machine learning pipelines. Unlike traditional approaches where the model dominates the workflow, NexusML treats the model as a central yet interchangeable component within a robust ecosystem of data pipelines, serving pipelines, and monitoring pipelines.

This project aims to provide a generalized MLOps solution that supports various machine learning models, enabling easy adaptation across different domains and architectures.

## Key Features

:white_check_mark: Modular Design – Easily swap different models while keeping the MLOps pipeline intact.

:white_check_mark: Data Pipeline Integration – Supports real-time and batch data processing with Kafka, Airflow, and PostgreSQL.

:white_check_mark: Model Serving – Deploy models efficiently with FastAPI, optimized for both batch inference and real-time predictions.

:white_check_mark: Continuous Monitoring – Track performance, detect data drift, and log experiments using Prometheus, Grafana, Loki, and MLflow.

:white_check_mark: CI/CD for MLOps – Automate deployment and model retraining with GitHub Actions, Jenkins, and MLflow Model Registry.

:white_check_mark: Scalability & Flexibility – Designed for deep learning, but extensible for any ML model, from classical to transformer-based architectures.

## Tech Stack

- Orchestration: Airflow, Jenkins
- Data Streaming & Storage: Kafka, PostgreSQL, MinIO
- Model Serving: FastAPI, TensorFlow Serving, TorchServe
- Monitoring & Logging: Prometheus, Grafana, Loki, MLflow
- CI/CD & Deployment: Docker, Kubernetes, GitHub Actions

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ThuanNaN/NexusML.git

git submodule update --init --recursive
```

## Future Roadmap

- [ ] Data pipeline
- [ ] Model Serving
- [ ] Continuous Monitoring
- [ ] CI/CD for MLOps
- [ ] Scalability & Flexibility

## Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request to improve NexusML.

## License

MIT License – Free to use and modify for any project.



git submodule update --init --recursive

jenkins: 44129f95515a48d3a0ceb3790b3136b7
jenkins - aivn2025

ngrok: 19522312@gm.uit.edu.vn
url: https://known-husky-allegedly.ngrok-free.app
plugin: 