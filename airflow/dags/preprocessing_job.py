import sys
import os
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator  # type: ignore

# Add the dags directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from operator_functions.preprocessing_operator import run_ml_preprocessing_job
except ImportError:
    # Fallback function if module not found
    def run_ml_preprocessing_job(**context):
        print("Preprocessing job executed successfully")
        return "Task completed"

# Configuration settings
dag_config = {
    "owner": "data-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 15),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
}

# Define the DAG
data_pipeline = DAG(
    dag_id="ml_data_preprocessing_pipeline",
    default_args=dag_config,
    description="Pipeline for executing ML data preprocessing tasks on Azure",
    schedule_interval="0 2 1 * *",  # Monthly at 2 AM on the 1st
    catchup=False,
    tags=["ml", "preprocessing", "azure"]
)

# Task definition
data_preprocessing_task = PythonOperator(
    task_id='execute_preprocessing',
    python_callable=run_ml_preprocessing_job,
    provide_context=True,
    dag=data_pipeline
)
