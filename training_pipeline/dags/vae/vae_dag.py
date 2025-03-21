import os
from datetime import datetime, timedelta
import yaml
import pandas as pd
import numpy as np
import os
import torch
import torch.nn as nn
from pathlib import Path
import pickle
from airflow import DAG
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def create_temp_dir():
    cuda_available = True if torch.cuda.is_available() else False
    print(f"Using GPU: {cuda_available}")
    path_save = Path("./vae_tmp_dir") / "v0.1"
    path_save.mkdir(parents=True, exist_ok=True)
    if not path_save.exists():
        raise FileNotFoundError(f"Failed to create directory: {path_save}")

with DAG(
    'vae_cnn_training_pipeline',
    default_args=default_args,
    description='A DAG to train and validate VAE_CNN model',
    schedule_interval=timedelta(days=1),
    ) as dag:

    create_temp_dir_task = PythonOperator(
        task_id='create_temp_dir',
        python_callable=create_temp_dir,
        dag=dag,
    )

    # data_processing_task = PythonOperator(
    #     task_id='data_processing',
    #     python_callable=data_processing,
    #     dag=dag,
    # )

    # train_model_task = PythonOperator(
    #     task_id='train_model',
    #     python_callable=train_model,
    #     dag=dag,
    # )

    # validate_model_task = PythonOperator(
    #     task_id='validate_model',
    #     python_callable=validate_model,
    #     dag=dag,
    # )
    
    # logging_artifacts_task = PythonOperator(
    #     task_id='logging_artifacts',
    #     python_callable=logging_artifacts,
    #     dag=dag,
    # )

# Define task dependencies
# data_processing >> train_model >> validate_model >> log_artifacts
