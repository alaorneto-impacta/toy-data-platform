from __future__ import annotations

import os
from datetime import datetime

from airflow import models
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models.baseoperator import chain

DAG_ID = "extract_movies"

DATASETS = ["imdb_top_1000", "meta_critic", "netflix_titles"]


env_vars = {
    "DESTINATION__FILESYSTEM__BUCKET_URL": "s3://raw",
    "DESTINATION__FILESYSTEM__CREDENTIALS__ENDPOINT_URL": "http://minio:9000",
    "DESTINATION__FILESYSTEM__CREDENTIALS__REGION_NAME": "us-east-1",
    "DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID": str(
        os.environ.get("DESTINATION__FILESYSTEM__CREDENTIALS__AWS_ACCESS_KEY_ID")
    ),
    "DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY": str(
        os.environ.get("DESTINATION__FILESYSTEM__CREDENTIALS__AWS_SECRET_ACCESS_KEY")
    ),
    "NORMALIZE__LOADER_FILE_FORMAT": "parquet",
    "PYICEBERG_CATALOG__RAW__URI": "http://lakekeeper:8181/catalog",
    "PYICEBERG_CATALOG__RAW__WAREHOUSE": "raw",
    "ICEBERG_CATALOG__ICEBERG_CATALOG_NAME": "raw",
    "ICEBERG_CATALOG__ICEBERG_CATALOG_TYPE": "rest",
}

with models.DAG(
    DAG_ID,
    schedule="@once",
    start_date=datetime(2025, 2, 1),
    catchup=False,
    tags=["movies", "full"],
) as dag:
    tasks = []
    for dataset in DATASETS:
        task = DockerOperator(
            docker_url="unix://var/run/docker.sock",
            image="my-dlt-pipeline:latest",
            command=["python", "filesystem_pipeline.py", "-t", dataset],
            network_mode="container:airflow_scheduler",
            task_id=f"ingestion-movies-{dataset}",
            auto_remove="force",
            dag=dag,
            environment={**env_vars},
        )
        tasks.append(task)

chain(*tasks)
