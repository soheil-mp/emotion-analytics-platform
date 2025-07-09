"""
Azure ML Hyperparameter Tuning Script.

This script defines and runs a hyperparameter sweep job on Azure Machine Learning
to optimize the DeBERTa-based multi-task emotion classification model.

Key functionalities:
- Defines a search space for key hyperparameters.
- Configures a sweep job using Azure ML's v2 SDK.
- Submits the job to find the best hyperparameter combination based on validation
F1 score.
"""

import os
import shutil
import tempfile
from contextlib import contextmanager

from azure.ai.ml import Input, MLClient, command
from azure.ai.ml.sweep import Choice, MedianStoppingPolicy, Uniform
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


@contextmanager
def create_temp_code_directory():
    """
    Context manager to create a temporary directory and copy required code folders.
    This ensures that only necessary code ('src' and 'models') is uploaded
    to Azure ML, keeping the context small and efficient.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Get the project root (assuming this script is in src/emotion_clf_pipeline)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # Define source and destination paths
        required_folders = ["src", "models"]
        for folder in required_folders:
            src_path = os.path.join(project_root, folder)
            dest_path = os.path.join(temp_dir, folder)
            if os.path.exists(src_path):
                shutil.copytree(src_path, dest_path)
            else:
                print(f"Warning: Source folder not found and not copied: {src_path}")

        # Copy paste the .env file
        env_path = os.path.join(project_root, ".env")
        if os.path.exists(env_path):
            shutil.copy(env_path, temp_dir)
        else:
            print(f"Warning: .env file not found and not copied: {env_path}")

        yield temp_dir
    finally:
        # Cleanup the temporary directory
        shutil.rmtree(temp_dir)


def main():
    """
    Defines and submits the Azure ML hyperparameter sweep job.
    """
    # Load environment variables from .env file to pass to the remote job
    load_dotenv()

    # --- Authenticate and get ML Client ---
    try:
        credential = DefaultAzureCredential()
        ml_client = MLClient.from_config(credential=credential)
    except Exception as e:
        print(f"Failed to create MLClient: {e}")
        print("Please ensure your Azure ML config file is present and correct.")
        return

    # Use the context manager to create a temporary code directory for the job
    with create_temp_code_directory() as temp_code_dir:
        # --- Define the command to run the training script ---
        training_command = command(
            code=temp_code_dir,  # Use the temporary directory as the code source
            command=(
                'python -c "import nltk; '
                "nltk.download('punkt', quiet=True); "
                "nltk.download('punkt_tab', quiet=True); "
                "nltk.download('averaged_perceptron_tagger', quiet=True); "
                "nltk.download('vader_lexicon', quiet=True); "
                "nltk.download('stopwords', quiet=True)\" && "
                "python -m src.emotion_clf_pipeline.train "
                "--train-data ${{inputs.train_data}} "
                "--test-data ${{inputs.test_data}} "
                "--learning-rate ${{search_space.learning_rate}} "
                "--weight-decay ${{search_space.weight_decay}} "
                "--dropout-prob ${{search_space.dropout_prob}} "
                "--hidden-dim ${{search_space.hidden_dim}} "
                "--output-dir ${{outputs.output_dir}}"
            ),
            inputs={
                "train_data": Input(
                    type="uri_file",
                    path="azureml:emotion-processed-train:17",
                    mode="ro_mount",
                ),
                "test_data": Input(
                    type="uri_file",
                    path="azureml:emotion-processed-test:17",
                    mode="ro_mount",
                ),
            },
            outputs={"output_dir": {"type": "uri_folder"}},
            environment="emotion-clf-pipeline-env:28",
            resources={
                "instance_type": "Standard_DS4_v2",
                "instance_count": 1,
            },
            display_name="deberta-hyperparameter-tuning-trial",
        )

        # --- Define the hyperparameter search space ---
        search_space = {
            "learning_rate": Uniform(min_value=1e-5, max_value=5e-5),
            "weight_decay": Uniform(min_value=0.01, max_value=0.1),
            "dropout_prob": Uniform(min_value=0.1, max_value=0.5),
            "hidden_dim": Choice([256, 512]),
        }

        # --- Configure the sweep job ---
        sweep_job = training_command.sweep(
            sampling_algorithm="random",
            search_space=search_space,
            goal="Maximize",
            primary_metric="val_f1_emotion",  # Must match the metric logged in train.py
            early_termination_policy=MedianStoppingPolicy(
                evaluation_interval=1, delay_evaluation=2
            ),
        )

        # --- Set a display name for the sweep job ---
        sweep_job.display_name = "deberta-hyperparameter-sweep"

        # --- Set limits for the sweep job ---
        sweep_job.set_limits(max_total_trials=4, max_concurrent_trials=1)

        # --- Submit the sweep job ---
        print("Submitting the hyperparameter sweep job to Azure ML...")
        returned_job = ml_client.jobs.create_or_update(
            sweep_job, experiment_name="emotion-clf-deberta-architecture"
        )
        print(f"Sweep job submitted. Job name: {returned_job.name}")
        print(f"You can view the job here: {returned_job.studio_url}")


if __name__ == "__main__":
    main()
