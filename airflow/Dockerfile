FROM apache/airflow:2.8.1-python3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl && apt-get clean
USER airflow

COPY dags/ ${AIRFLOW_HOME}/dags
