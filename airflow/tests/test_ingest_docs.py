import pytest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure the dags directory is in the path so we can import ingest_docs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dags"))

# Mock airflow and DockerOperator
class DummyTask:
    def __init__(self, task_id, **kwargs):
        self.task_id = task_id
        self.kwargs = kwargs

class DummyDAG:
    def __init__(self, dag_id, **kwargs):
        self.dag_id = dag_id
        self.tasks = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

mock_airflow = MagicMock()
mock_airflow.DAG = DummyDAG
sys.modules['airflow'] = mock_airflow
sys.modules['airflow.providers'] = MagicMock()
sys.modules['airflow.providers.docker'] = MagicMock()
sys.modules['airflow.providers.docker.operators'] = MagicMock()
mock_docker_operator = MagicMock()
mock_docker_operator.DockerOperator = DummyTask
sys.modules['airflow.providers.docker.operators.docker'] = mock_docker_operator

mock_docker_types = MagicMock()
mock_docker_types.Mount = MagicMock()
sys.modules['docker'] = MagicMock()
sys.modules['docker.types'] = mock_docker_types

from dags.ingest_docs import dag, ingestion_task

def test_dag_loaded():
    assert dag is not None
    assert dag.dag_id == "ingest_hp_manuals_to_pgvector"
    assert ingestion_task is not None
    assert ingestion_task.task_id == "process_and_embed_documents"
    assert ingestion_task.kwargs.get('image') == 'simple_rag_worker:latest'
    assert ingestion_task.kwargs.get('network_mode') == 'simple_rag_default'
