FROM apache/airflow:2.10.3-python3.11
COPY mlops_msr/app_requirements.txt .
COPY mlflow_and_sp.env .
# COPY mlflow_and_sp.env .
RUN pip install -r app_requirements.txt