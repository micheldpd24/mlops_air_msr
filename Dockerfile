FROM apache/airflow:2.10.3-python3.11
COPY mlops_msr/app_requirements.txt .
COPY .env .
RUN pip install -r app_requirements.txt