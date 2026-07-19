from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Configuration variables
# We must use the absolute path on the host because Docker daemon runs on the host.
HOST_DATA_DIRECTORY = "/home/matheus/Documents/simple_rag/data"

default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ingest_hp_manuals_to_pgvector',
    default_args=default_args,
    description='Extracts HP manuals, chunks text, and stores embeddings in PostgreSQL via DockerOperator',
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['rag', 'ingestion', 'hp_project'],
) as dag:

    ingestion_task = DockerOperator(
        task_id='process_and_embed_documents',
        image='simple_rag_worker:latest',
        api_version='auto',
        auto_remove='force',
        docker_url='unix://var/run/docker.sock',
        network_mode='simple_rag_default',
        environment={
            'OPENAI_API_KEY': 'sk-local-dev-key',
            'OPENAI_BASE_URL': 'http://model-server:8080/v1',
            'EMBEDDING_MODEL': 'BAAI/bge-small-en-v1.5'
        },
        mounts=[
            Mount(source=HOST_DATA_DIRECTORY, target='/opt/data', type='bind', read_only=True)
        ],
        mount_tmp_dir=False
    )