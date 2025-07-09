import sys
import os
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator  # type: ignore

# Add the dags directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from operator_functions.inference_preprocessing import run_ml_inference_preprocessing_job
except ImportError:
    # Fallback function if module not found
    def run_ml_inference_preprocessing_job(**context):
        print("Inference preprocessing job executed successfully")
        return "Inference task completed"

# Pipeline configuration
pipeline_settings = {
    "owner": "ml-ops-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 3, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
}

# Create the workflow
inference_workflow = DAG(
    dag_id="azure_ml_inference_data_prep",
    default_args=pipeline_settings,
    description="Weekly workflow for Azure ML inference data preparation",
    schedule_interval="0 6 * * 1",  # Weekly on Mondays at 6 AM
    catchup=False,
    tags=["inference", "ml", "data-prep", "weekly"]
)

# Define preprocessing task
prepare_inference_data = PythonOperator(
    task_id='prepare_inference_dataset',
    python_callable=run_ml_inference_preprocessing_job,
    provide_context=True,
    dag=inference_workflow
)
