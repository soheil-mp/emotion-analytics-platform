"""
Azure ML Pipeline Integration for Emotion Classification Pipeline.

This module handles Azure ML pipeline submission and monitoring for:
- Data preprocessing pipelines
- Model training pipelines
- Job status monitoring

Integrates with existing Azure ML resources including compute instances,
environments, and data assets.
"""

import logging
import os
import shutil
import tempfile
import time
from types import SimpleNamespace
from typing import Dict, Optional

# ==============================================================================
# COMPUTE CONFIGURATION - Switch between compute options
# ==============================================================================
# Set COMPUTE_MODE to either "lambda" or "serverless" to switch compute targets
COMPUTE_MODE = "lambda"  # Options: "lambda", "serverless"

# Compute configurations
COMPUTE_CONFIGS = {
    "lambda": {
        "name": "adsai-lambda-0",
        "type": "compute_instance",
        "description": "Existing compute instance adsai-lambda-0",
    },
    "serverless": {
        "name": "serverless-ds4v2",
        "type": "serverless",
        "vm_size": "Standard_DS4_v2",
        "instance_count": 1,
        "priority": "Dedicated",
        "description": "Serverless compute with Standard_DS4_v2",
    },
}

# Set active compute configuration based on mode
ACTIVE_COMPUTE_CONFIG = COMPUTE_CONFIGS[COMPUTE_MODE]
COMPUTE_NAME = ACTIVE_COMPUTE_CONFIG["name"]

# Azure ML Configuration
ENV_NAME, ENV_VERSION = "emotion-clf-pipeline-env", "28"

# Data assets
# The latest version of these assets will be fetched automatically.
RAW_TRAIN_DATA_ASSET_NAME = "emotion-raw-train"
RAW_TEST_DATA_ASSET_NAME = "emotion-raw-test"

logger = logging.getLogger(__name__)

try:
    from azure.ai.ml import Input, MLClient, Output, command, dsl
    from azure.ai.ml.constants import AssetTypes
    from azure.ai.ml.entities import (
        CommandComponent,
        CronTrigger,
        Data,
        Job,
        JobSchedule,
        ResourceConfiguration,
    )
    from azure.identity import DefaultAzureCredential

    AZURE_AVAILABLE = True
except ImportError:
    logger.warning("Azure ML SDK not available. Install with: pip install azure-ai-ml")
    AZURE_AVAILABLE = False


def get_ml_client() -> MLClient:
    """Get Azure ML client with authentication."""
    if not AZURE_AVAILABLE:
        raise ImportError("Azure ML SDK not available")  # Read Azure ML configuration
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    workspace_name = os.getenv("AZURE_WORKSPACE_NAME")

    if not all([subscription_id, resource_group, workspace_name]):
        raise ValueError("Missing Azure ML configuration environment variables")

    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        workspace_name=workspace_name,
    )

    return ml_client


def list_available_compute_targets(ml_client: MLClient) -> Dict[str, str]:
    """
    List all available compute targets in the Azure ML workspace.

    Returns:
        Dict[str, str]: Dictionary mapping compute target names to their current state
    """
    try:
        compute_targets = {}
        for compute in ml_client.compute.list():
            compute_targets[compute.name] = compute.provisioning_state
            logger.info(
                f"Compute target: {compute.name} - State: {compute.provisioning_state}"
            )
        return compute_targets
    except Exception as e:
        logger.error(f"Failed to list compute targets: {e}")
        return {}


def validate_compute_target(ml_client: MLClient, compute_name: str) -> bool:
    """
    Validate that a compute target exists and is available.

    Args:
        ml_client: Azure ML client
        compute_name: Name of the compute target to validate

    Returns:
        bool: True if compute target is available, False otherwise
    """
    try:
        logger.info(f"Validating compute target: {compute_name}")
        compute = ml_client.compute.get(compute_name)
        state = compute.provisioning_state
        logger.info(f"Compute target {compute_name} found - State: {state}")

        # Check if compute is in a usable state
        if state.lower() in ["succeeded", "running"]:
            logger.info(f"✅ Compute target {compute_name} is available")
            return True
        else:
            logger.warning(f"⚠️ Compute target {compute_name} is in state: {state}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to validate compute target {compute_name}: {e}")
        return False


def get_fallback_compute_target(ml_client: MLClient) -> Optional[str]:
    """
    Find an available fallback compute target if the primary one is unavailable.

    Returns:
        Optional[str]: Name of an available compute target, None if none available
    """
    try:
        compute_targets = list_available_compute_targets(ml_client)

        # Look for compute targets in good states
        for name, state in compute_targets.items():
            if state.lower() in ["succeeded", "running"]:
                logger.info(f"Found available fallback compute target: {name}")
                return name

        logger.warning("No available fallback compute targets found")
        return None
    except Exception as e:
        logger.error(f"Failed to find fallback compute target: {e}")
        return None


def get_compute_target() -> str:
    """
    Get the appropriate compute target based on current configuration.

    Returns:
        str: The compute target name to use
    """
    config = ACTIVE_COMPUTE_CONFIG
    logger.info(f"🔧 Using compute mode: {COMPUTE_MODE}")
    logger.info(f"🎯 Compute target: {config['name']} ({config['description']})")
    return config["name"]


def ensure_serverless_compute_available(ml_client: MLClient) -> bool:
    """
    Ensure serverless compute is available for use.
    For serverless compute, no explicit creation is needed - it's provisioned on-demand.

    Args:
        ml_client: Azure ML client

    Returns:
        bool: True if serverless compute is available/configured, False otherwise
    """
    if COMPUTE_MODE != "serverless":
        return True

    try:
        config = ACTIVE_COMPUTE_CONFIG
        logger.info(f"✅ Serverless compute configured: {config['vm_size']}")
        logger.info(f"   Instance count: {config['instance_count']}")
        logger.info(f"   Priority: {config['priority']}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to configure serverless compute: {e}")
        return False


def get_compute_for_job() -> str:
    """
    Get the compute target for job submission with proper validation.

    Returns:
        str: The compute target to use for the job, or None for serverless
    """
    ml_client = get_ml_client()

    if COMPUTE_MODE == "serverless":
        # For serverless, ensure configuration is valid but return None
        # to omit compute parameter
        if not ensure_serverless_compute_available(ml_client):
            raise RuntimeError("Serverless compute configuration failed")
        logger.info("🎯 Using serverless compute (omitting compute parameter)")
        return None  # Return None to omit compute parameter for serverless
    else:
        # For compute instances, validate availability
        compute_to_use = get_compute_target()
        logger.info(f"🔍 Validating compute target: {compute_to_use}")
        if not validate_compute_target(ml_client, compute_to_use):
            logger.warning(f"❌ Primary compute target {compute_to_use} unavailable")
            # Try to find a fallback
            fallback_compute = get_fallback_compute_target(ml_client)
            if fallback_compute:
                logger.info(f"🔄 Using fallback compute target: {fallback_compute}")
                return fallback_compute
            else:
                raise RuntimeError("No available compute targets found")
        else:
            logger.info(f"✅ Using primary compute target: {compute_to_use}")
            return compute_to_use


def submit_preprocess_pipeline(args) -> Job:
    """Submit data preprocessing pipeline to Azure ML."""
    ml_client = get_ml_client()

    # Get latest versions of data assets
    try:
        raw_train_version = ml_client.data.get(
            name=RAW_TRAIN_DATA_ASSET_NAME, label="latest"
        ).version
        raw_test_version = ml_client.data.get(
            name=RAW_TEST_DATA_ASSET_NAME, label="latest"
        ).version
        logger.info(
            f"Using data version '{raw_train_version}' for training data asset "
            f"'{RAW_TRAIN_DATA_ASSET_NAME}'."
        )
        logger.info(
            f"Using data version '{raw_test_version}' for test data asset "
            f"'{RAW_TEST_DATA_ASSET_NAME}'."
        )
    except Exception as e:
        logger.error(
            f"Failed to retrieve latest data asset versions. Please ensure that "
            f"the data assets '{RAW_TRAIN_DATA_ASSET_NAME}' and "
            f"'{RAW_TEST_DATA_ASSET_NAME}' exist and have a 'latest' tag. "
            f"Error: {e}"
        )
        raise

    # Step 1: Get appropriate compute target
    compute_to_use = get_compute_for_job()

    # Create temporary directory with required files
    temp_dir = create_temp_code_directory()

    try:
        # Define preprocessing command job
        job_kwargs = {
            "code": temp_dir,
            "command": (
                'python -c "import nltk; '
                "nltk.download('punkt', quiet=True); "
                "nltk.download('punkt_tab', quiet=True); "
                "nltk.download('averaged_perceptron_tagger', quiet=True); "
                "nltk.download('vader_lexicon', quiet=True); "
                "nltk.download('stopwords', quiet=True)\" "
                "&& python -m src.emotion_clf_pipeline.data "
                f"--raw-train-path ${{inputs.train_data}} "
                f"--raw-test-path ${{inputs.test_data}} "
                f"--output-dir ${{outputs.processed_data}} "
                f"--encoders-dir ${{outputs.encoders}} "
                f"--model-name-tokenizer {args.model_name_tokenizer} "
                f"--max-length {args.max_length} "
                f"--output-tasks {args.output_tasks}"
            ),
            "inputs": {
                "train_data": Input(
                    type=AssetTypes.URI_FOLDER,
                    path=f"azureml:{RAW_TRAIN_DATA_ASSET_NAME}:{raw_train_version}",  # noqa: E501
                ),
                "test_data": Input(
                    type=AssetTypes.URI_FOLDER,
                    path=f"azureml:{RAW_TEST_DATA_ASSET_NAME}:{raw_test_version}",  # noqa: E501
                ),
            },
            "outputs": {
                "processed_data": Output(type=AssetTypes.URI_FOLDER),
                "encoders": Output(type=AssetTypes.URI_FOLDER),
            },
            "environment": f"azureml:{ENV_NAME}:{ENV_VERSION}",
            "display_name": "deberta-data-preprocessing-pipeline",
            "description": "Data preprocessing pipeline + Register to data assets",
        }

        # Add compute parameter only if not using serverless
        if compute_to_use is not None:
            job_kwargs["compute"] = compute_to_use

        # Create the job
        job = command(**job_kwargs)

        # For serverless compute, add resource configuration
        if COMPUTE_MODE == "serverless":
            config = ACTIVE_COMPUTE_CONFIG
            job.resources = ResourceConfiguration(
                instance_type=config["vm_size"], instance_count=config["instance_count"]
            )
            logger.info(
                f"🎯 Configured serverless resources: "
                f"{config['vm_size']} x{config['instance_count']}"
            )

        # Submit job
        experiment_name = "emotion-clf-deberta-architecture"
        job = ml_client.jobs.create_or_update(job, experiment_name=experiment_name)
        logger.info(f"Submitted preprocessing job: {job.name}")

        return job

    finally:
        # Clean up temporary directory after job submission
        cleanup_temp_directory(temp_dir)


def submit_training_pipeline(args) -> Job:
    """Submit model training pipeline to Azure ML."""
    ml_client = get_ml_client()

    # Step 1: Get appropriate compute target
    compute_to_use = get_compute_for_job()

    # Create temporary directory with required files
    temp_dir = create_temp_code_directory()

    try:
        # Define training command job
        job_kwargs = {
            "code": temp_dir,
            "command": (
                'python -c "import nltk; '
                "nltk.download('punkt', quiet=True); "
                "nltk.download('punkt_tab', quiet=True); "
                "nltk.download('averaged_perceptron_tagger', quiet=True); "
                "nltk.download('vader_lexicon', quiet=True); "
                "nltk.download('stopwords', quiet=True)\" "
                "&& python -m src.emotion_clf_pipeline.train "
                f"--model-name {args.model_name} "
                f"--batch-size {args.batch_size} "
                f"--learning-rate {args.learning_rate} "
                f"--epochs {args.epochs} "
                "--train-data ${{inputs.train_data}} "
                "--test-data ${{inputs.test_data}} "
                "--output-dir ${{outputs.model_output}}"
            ),
            "environment": f"azureml:{ENV_NAME}:{ENV_VERSION}",
            "inputs": {
                "train_data": Input(
                    type="uri_file", path="azureml:emotion-processed-train:1"
                ),
                "test_data": Input(
                    type="uri_file", path="azureml:emotion-processed-test:1"
                ),
            },
            "outputs": {"model_output": Output(type="uri_folder", mode="rw_mount")},
            "display_name": "deberta-training-and-evaluation-pipeline",
            "description": "Model training for emotion classification",
        }

        # Add compute parameter only if not using serverless
        if compute_to_use is not None:
            job_kwargs["compute"] = compute_to_use

        # Create the job
        job = command(**job_kwargs)

        # For serverless compute, add resource configuration
        if COMPUTE_MODE == "serverless":
            config = ACTIVE_COMPUTE_CONFIG
            job.resources = ResourceConfiguration(
                instance_type=config["vm_size"], instance_count=config["instance_count"]
            )
            logger.info(
                f"🎯 Configured serverless resources: "
                f"{config['vm_size']} x{config['instance_count']}"
            )

        # Submit job
        job = ml_client.jobs.create_or_update(
            job, experiment_name="emotion-clf-deberta-architecture"
        )
        logger.info(f"Submitted training job: {job.name}")

        return job

    finally:
        # Clean up temporary directory after job submission
        cleanup_temp_directory(temp_dir)


def get_pipeline_status(job_id: str) -> str:
    """Get the status of an Azure ML job."""
    ml_client = get_ml_client()

    try:
        job = ml_client.jobs.get(job_id)
        return job.status
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        return "Unknown"


def list_recent_jobs(limit: int = 10) -> list:
    """List recent Azure ML jobs."""
    ml_client = get_ml_client()

    try:
        jobs = list(ml_client.jobs.list(max_results=limit))
        return jobs
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        return []


def download_job_outputs(job_id: str, output_path: str = "./outputs") -> bool:
    """Download outputs from an Azure ML job."""
    ml_client = get_ml_client()

    try:
        # Create output directory
        os.makedirs(output_path, exist_ok=True)

        # Download job outputs
        ml_client.jobs.download(job_id, download_path=output_path)
        logger.info(f"Downloaded job outputs to: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to download job outputs: {str(e)}")
        return False


def create_data_asset(name: str, path: str, description: str = "") -> Optional[Data]:
    """Create or update a data asset in Azure ML."""
    ml_client = get_ml_client()

    try:
        data_asset = Data(
            name=name, path=path, type=AssetTypes.URI_FOLDER, description=description
        )

        created_data = ml_client.data.create_or_update(data_asset)
        logger.info(f"Created data asset: {created_data.name}")
        return created_data

    except Exception as e:
        logger.error(f"Failed to create data asset: {str(e)}")
        return None


def get_compute_status(compute_name: str) -> str:
    """Get the status of an Azure ML compute resource."""
    ml_client = get_ml_client()

    try:
        compute = ml_client.compute.get(compute_name)
        return compute.provisioning_state
    except Exception as e:
        logger.error(f"Failed to get compute status: {str(e)}")
        return "Unknown"


# Configuration helpers
def validate_azure_config() -> bool:
    """Validate Azure ML configuration."""
    required_vars = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP",
        "AZURE_WORKSPACE_NAME",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False

    return True


def get_azure_config() -> Dict[str, str]:
    """Get current Azure ML configuration."""
    return {
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID", ""),
        "resource_group": os.getenv("AZURE_RESOURCE_GROUP", ""),
        "workspace_name": os.getenv("AZURE_WORKSPACE_NAME", ""),
        "tenant_id": os.getenv("AZURE_TENANT_ID", ""),
    }


def create_temp_code_directory() -> str:
    """
    Create a temporary directory with only the required files for Azure ML.

    Returns:
        str: Path to the temporary directory
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="azureml_code_")

    try:  # Copy entire src directory to preserve structure
        shutil.copytree("./src", os.path.join(temp_dir, "src"))

        # Copy models/features directory (contains EmoLex lexicon)
        models_dest = os.path.join(temp_dir, "models")
        os.makedirs(models_dest, exist_ok=True)

        if os.path.exists("./models/features"):
            features_dest = os.path.join(models_dest, "features")
            shutil.copytree("./models/features", features_dest)

        # Copy models/encoders directory if it exists
        if os.path.exists("./models/encoders"):
            encoders_dest = os.path.join(models_dest, "encoders")
            shutil.copytree("./models/encoders", encoders_dest)

        # Copy poetry files for dependency installation in the job
        shutil.copy2("./pyproject.toml", temp_dir)
        shutil.copy2("./poetry.lock", temp_dir)

        # Copy .env file if it exists for environment variables
        if os.path.exists("./.env"):
            shutil.copy2("./.env", os.path.join(temp_dir, ".env"))
            logger.info("Copied .env file to temporary code directory.")

        logger.info(f"Created temporary code directory: {temp_dir}")
        return temp_dir

    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError(f"Failed to create temporary directory: {str(e)}")


def cleanup_temp_directory(temp_dir: str) -> None:
    """Clean up temporary directory."""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary directory: {str(e)}")


def register_processed_data_assets(job: Job) -> bool:
    """
    Wait for preprocessing job to complete and register outputs as data assets.

    Args:
        job: The preprocessing job to monitor

    Returns:
        bool: True if successful, False otherwise
    """
    try:

        ml_client = get_ml_client()

        # Wait for job completion
        logger.info(f"Waiting for job {job.name} to complete...")
        start_time = time.time()
        timeout = 3600  # 1 hour timeout

        while job.status not in ["Completed", "Failed", "Canceled"]:
            if time.time() - start_time > timeout:
                logger.error(f"Job {job.name} timed out after {timeout} seconds")
                return False

            time.sleep(30)  # Check every 30 seconds
            job = ml_client.jobs.get(job.name)
            logger.info(f"Job status: {job.status}")

        if job.status != "Completed":
            logger.error(f"Job {job.name} failed with status: {job.status}")
            return False

        logger.info(f"Job {job.name} completed successfully!")

        # Get job outputs
        processed_data_output = job.outputs.get("processed_data")
        if not processed_data_output:
            logger.error("No processed_data output found in job")
            return False

        # Download the processed data to a temporary location
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info("Downloading processed data from job outputs...")

            # Download the processed data folder
            ml_client.jobs.download(
                job.name, output_name="processed_data", download_path=temp_dir
            )

            # Check possible paths for downloaded data
            # Azure ML may download directly to temp_dir or create subdirectories
            possible_paths = [
                os.path.join(temp_dir, "processed_data"),  # Expected path
                temp_dir,  # Direct download to temp_dir
                os.path.join(temp_dir, "named-outputs", "processed_data"),
            ]

            processed_data_path = None
            for path in possible_paths:
                logger.info(f"Checking for processed data at: {path}")
                if os.path.exists(path):
                    # Check if this path contains the expected CSV files
                    train_csv = os.path.join(path, "train.csv")
                    test_csv = os.path.join(path, "test.csv")
                    if os.path.exists(train_csv) and os.path.exists(test_csv):
                        processed_data_path = path
                        logger.info(f"Found processed data at: {processed_data_path}")
                        break
                    else:
                        logger.info(
                            f"Path exists but doesn't contain train.csv and test.csv: "
                            f"{path}"
                        )

            if not processed_data_path:
                # List contents of temp_dir for debugging
                logger.error(f"Processed data not found. Contents of {temp_dir}:")
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    if os.path.isdir(item_path):
                        logger.error(f"  Directory: {item}/")
                        for subitem in os.listdir(item_path):
                            logger.error(f"    {subitem}")
                    else:
                        logger.error(f"  File: {item}")
                return False  # Check for train.csv and test.csv
            train_csv_path = os.path.join(processed_data_path, "train.csv")
            test_csv_path = os.path.join(processed_data_path, "test.csv")

            if not os.path.exists(train_csv_path):
                logger.error(f"train.csv not found at: {train_csv_path}")
                return False

            if not os.path.exists(test_csv_path):
                logger.error(f"test.csv not found at: {test_csv_path}")
                return False

            # Register train data asset (as UriFile pointing to CSV)
            logger.info("Registering emotion-processed-train data asset...")
            train_data_asset = Data(
                name="emotion-processed-train",
                description="Processed training data for emotion classification",
                path=train_csv_path,
                type=AssetTypes.URI_FILE,
            )

            train_asset = ml_client.data.create_or_update(train_data_asset)
            logger.info(
                f"✅ Registered train data asset: {train_asset.name} "
                f"(version: {train_asset.version})"
            )

            # Register test data asset (as UriFile pointing to CSV)
            logger.info("Registering emotion-processed-test data asset...")
            test_data_asset = Data(
                name="emotion-processed-test",
                description="Processed test data for emotion classification",
                path=test_csv_path,
                type=AssetTypes.URI_FILE,
            )

            test_asset = ml_client.data.create_or_update(test_data_asset)
            logger.info(
                f"✅ Registered test data asset: {test_asset.name} "
                f"(version: {test_asset.version})"
            )

        logger.info("Successfully registered processed data assets!")
        return True

    except Exception as e:
        logger.error(f"Failed to register processed data assets: {str(e)}")
        logger.error("Full error traceback:", exc_info=True)
        return False


def register_processed_data_assets_from_paths(
    train_csv_path: str, test_csv_path: str
) -> bool:
    """
    Register processed data files as Azure ML data assets from their paths.

    Args:
        train_csv_path: The local path to the processed train.csv file.
        test_csv_path: The local path to the processed test.csv file.

    Returns:
        bool: True if registration is successful, False otherwise.
    """
    try:

        ml_client = get_ml_client()

        # Register train data asset
        logger.info(f"Registering train data asset from: {train_csv_path}")
        train_data_asset = Data(
            name="emotion-processed-train",
            description="Processed training data for emotion classification",
            path=train_csv_path,
            type=AssetTypes.URI_FILE,
        )
        train_asset = ml_client.data.create_or_update(train_data_asset)
        logger.info(
            f"✅ Registered train data asset: {train_asset.name} "
            f"(version: {train_asset.version})"
        )

        # Register test data asset
        logger.info(f"Registering test data asset from: {test_csv_path}")
        test_data_asset = Data(
            name="emotion-processed-test",
            description="Processed test data for emotion classification",
            path=test_csv_path,
            type=AssetTypes.URI_FILE,
        )
        test_asset = ml_client.data.create_or_update(test_data_asset)
        logger.info(
            f"✅ Registered test data asset: {test_asset.name} "
            f"(version: {test_asset.version})"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to register processed data assets from paths: {str(e)}")
        logger.error("Full error traceback:", exc_info=True)
        return False


def submit_complete_pipeline(args) -> Job:
    """
    Submit a complete end-to-end training pipeline to Azure ML.
    This pipeline includes data preprocessing and model training steps.
    """

    ml_client = get_ml_client()

    # Get latest versions of data assets
    try:
        raw_train_version = ml_client.data.get(
            name=RAW_TRAIN_DATA_ASSET_NAME, label="latest"
        ).version
        raw_test_version = ml_client.data.get(
            name=RAW_TEST_DATA_ASSET_NAME, label="latest"
        ).version
        logger.info(
            f"Using data version '{raw_train_version}' for training data asset "
            f"'{RAW_TRAIN_DATA_ASSET_NAME}'."
        )
        logger.info(
            f"Using data version '{raw_test_version}' for test data asset "
            f"'{RAW_TEST_DATA_ASSET_NAME}'."
        )
    except Exception as e:
        logger.error(
            f"Failed to retrieve latest data asset versions. Please ensure that "
            f"the data assets '{RAW_TRAIN_DATA_ASSET_NAME}' and "
            f"'{RAW_TEST_DATA_ASSET_NAME}' exist and have a 'latest' tag. "
            f"Error: {e}"
        )
        raise

    # Step 1: Get appropriate compute target
    compute_to_use = get_compute_for_job()

    # Create a temporary directory with the necessary code
    temp_dir = create_temp_code_directory()

    try:
        # Define Preprocessing Component
        preprocess_command = (
            "python -c \"import nltk; nltk.download('punkt', quiet=True); "
            "nltk.download('punkt_tab', quiet=True); "
            "nltk.download('wordnet', quiet=True); "
            "nltk.download('omw-1.4', quiet=True); "
            "nltk.download('averaged_perceptron_tagger', quiet=True); "
            "nltk.download('vader_lexicon', quiet=True); "
            "nltk.download('stopwords', quiet=True)\" "
            "&& python -m src.emotion_clf_pipeline.data "
            "--raw-train-path ${{inputs.raw_train_data}} "
            "--raw-test-path ${{inputs.raw_test_data}} "
            "--output-dir ${{outputs.processed_data}} "
            "--encoders-dir ${{outputs.encoders}} "
            f"--model-name-tokenizer {args.model_name_tokenizer} "
            f"--max-length {args.max_length} "
            f"--output-tasks {args.output_tasks}"
        )
        if args.register_data_assets:
            preprocess_command += " --register-data-assets"

        preprocess_component = CommandComponent(
            name="preprocess_data",
            display_name="DeBERTa Data Preprocessing Pipeline",
            description="Tokenizes and preprocesses raw text data.",
            inputs={
                "raw_train_data": Input(type=AssetTypes.URI_FOLDER),
                "raw_test_data": Input(type=AssetTypes.URI_FOLDER),
            },
            outputs={
                "processed_data": Output(type=AssetTypes.URI_FOLDER),
                "encoders": Output(type=AssetTypes.URI_FOLDER),
            },
            command=preprocess_command,
            environment=f"azureml:{ENV_NAME}:{ENV_VERSION}",
            code=temp_dir,
        )

        # Define Training Component
        train_command = (
            "python -c \"import nltk; nltk.download('punkt', quiet=True); "
            "nltk.download('punkt_tab', quiet=True); "
            "nltk.download('wordnet', quiet=True); "
            "nltk.download('omw-1.4', quiet=True); "
            "nltk.download('averaged_perceptron_tagger', quiet=True); "
            "nltk.download('vader_lexicon', quiet=True); "
            "nltk.download('stopwords', quiet=True)\" "
            "&& python -m src.emotion_clf_pipeline.train "
            "--train-data ${{inputs.processed_data}}/train.csv "
            "--test-data ${{inputs.processed_data}}/test.csv "
            "--encoders-dir ${{inputs.encoders}} "
            f"--model-name {args.model_name} "
            f"--batch-size {args.batch_size} "
            f"--learning-rate {args.learning_rate} "
            f"--epochs {args.epochs} "
            "--output-dir ${{outputs.trained_model}} "
            "# Cache-busting comment"
        )

        train_component = CommandComponent(
            name="train_emotion_classifier_v2",
            display_name="DeBERTa Training and Evaluation Pipeline",
            description="Trains a transformer model for emotion classification.",
            inputs={
                "processed_data": Input(type=AssetTypes.URI_FOLDER),
                "encoders": Input(type=AssetTypes.URI_FOLDER),
            },
            outputs={
                "trained_model": Output(type=AssetTypes.URI_FOLDER),
                "metrics_file": Output(type=AssetTypes.URI_FILE),
            },
            command=train_command,
            environment=f"azureml:{ENV_NAME}:{ENV_VERSION}",
            code=temp_dir,
        )

        # Define the pipeline
        pipeline_kwargs = {
            "description": "End-to-end pipeline for emotion classification training",
        }

        # Set compute configuration based on mode
        if COMPUTE_MODE == "serverless":
            # For serverless pipelines, use default_compute="serverless"
            pipeline_kwargs["default_compute"] = "serverless"
            logger.info("🎯 Pipeline configured for serverless compute")
        else:
            # For compute instances, use the compute target
            pipeline_kwargs["compute"] = compute_to_use
            logger.info(f"🎯 Pipeline configured for compute: {compute_to_use}")

        @dsl.pipeline(**pipeline_kwargs)
        def emotion_clf_pipeline(
            raw_train_data: Input,
            raw_test_data: Input,
        ):
            preprocess_job = preprocess_component(
                raw_train_data=raw_train_data,
                raw_test_data=raw_test_data,
            )
            preprocess_job.display_name = "preprocess-job"

            train_and_eval_job = train_component(
                processed_data=preprocess_job.outputs.processed_data,
                encoders=preprocess_job.outputs.encoders,
            )
            train_and_eval_job.display_name = "train-and-eval-job"

            return {
                "pipeline_processed_data": preprocess_job.outputs.processed_data,
                "pipeline_trained_model": train_and_eval_job.outputs.trained_model,
            }

        # Instantiate the pipeline
        pipeline_job = emotion_clf_pipeline(
            raw_train_data=Input(
                type=AssetTypes.URI_FOLDER,
                path=(f"azureml:{RAW_TRAIN_DATA_ASSET_NAME}:{raw_train_version}"),
            ),
            raw_test_data=Input(
                type=AssetTypes.URI_FOLDER,
                path=(f"azureml:{RAW_TEST_DATA_ASSET_NAME}:{raw_test_version}"),
            ),
        )

        # Configure serverless resources if needed
        if COMPUTE_MODE == "serverless":
            config = ACTIVE_COMPUTE_CONFIG
            # Set resources for the entire pipeline
            pipeline_job.settings.default_datastore = None
            pipeline_job.settings.default_compute = "serverless"
            logger.info(
                f"🎯 Configured pipeline for serverless with VM size: "
                f"{config['vm_size']}"
            )

        # Submit the pipeline job
        pipeline_job.display_name = f"{args.pipeline_name}"
        job = ml_client.jobs.create_or_update(
            pipeline_job, experiment_name="emotion-clf-deberta-architecture"
        )

        logger.info(f"Submitted pipeline job: {job.name}")
        logger.info(f"View in Azure ML Studio: {job.studio_url}")

        return job

    finally:
        # Clean up temporary code directory
        cleanup_temp_directory(temp_dir)


# ==============================================================================
# AZURE ML SCHEDULING FUNCTIONALITY
# ==============================================================================


def create_pipeline_schedule(
    pipeline_name: str,
    schedule_name: str,
    cron_expression: str = "0 0 * * *",  # Daily at midnight
    timezone: str = "UTC",
    description: str = None,
    enabled: bool = True,
    args=None,
) -> Optional[str]:
    """
    Create a scheduled pipeline in Azure ML.

    Args:
        pipeline_name: Name of the pipeline to schedule
        schedule_name: Name for the schedule
        cron_expression: Cron expression for scheduling (default: daily at midnight)
        timezone: Timezone for the schedule (default: UTC)
        description: Description for the schedule
        enabled: Whether the schedule should be enabled
        args: Pipeline arguments (if None, uses default settings)

    Returns:
        Schedule ID if successful, None otherwise

    Example cron expressions:
        - "0 0 * * *": Daily at midnight
        - "0 0 * * 0": Weekly on Sunday at midnight
        - "0 */6 * * *": Every 6 hours
        - "0 0 1 * *": Monthly on the 1st at midnight
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure ML SDK not available for scheduling")
        return None

    try:
        ml_client = get_ml_client()

        # Set default args if not provided
        if args is None:
            args = SimpleNamespace(
                pipeline_name=pipeline_name,
                model_name_tokenizer="microsoft/deberta-v3-base",
                max_length=128,
                output_tasks="emotion,sub_emotion,intensity",
                register_data_assets=True,
                model_name="microsoft/deberta-v3-xsmall",
                batch_size=16,
                learning_rate=2e-5,
                epochs=1,
                registration_f1_threshold=0.10,
            )

        # Create the pipeline job first (without submitting)
        pipeline_job = _create_pipeline_job(args)

        # Create cron trigger
        cron_trigger = CronTrigger(expression=cron_expression, time_zone=timezone)

        # Create the job schedule
        job_schedule = JobSchedule(
            name=schedule_name,
            trigger=cron_trigger,
            create_job=pipeline_job,
            description=description or f"Scheduled execution of {pipeline_name}",
            is_enabled=enabled,
            tags={
                "pipeline_type": "emotion_classification",
                "created_by": "emotion_clf_pipeline",
                "schedule_type": "cron",
            },
        )

        # Create the schedule in Azure ML
        created_schedule_poller = ml_client.schedules.begin_create_or_update(
            job_schedule
        )
        created_schedule = created_schedule_poller.result()  # Wait for completion

        logger.info(
            f"✅ Created schedule '{schedule_name}' for pipeline '{pipeline_name}'"
        )
        logger.info(f"   📅 Cron: {cron_expression} ({timezone})")
        logger.info(f"   🔄 Enabled: {enabled}")
        logger.info(f"   📍 Schedule ID: {created_schedule.name}")

        return created_schedule.name

    except Exception as e:
        logger.error(f"❌ Failed to create pipeline schedule: {e}")
        return None


def _create_pipeline_job(args):
    """
    Create a pipeline job configuration for scheduling.
    This is similar to submit_complete_pipeline but returns the job config
    instead of submitting.
    """

    ml_client = get_ml_client()

    # Get latest versions of data assets
    # For scheduled jobs, this resolves the version at schedule creation time.
    # The pipeline will use this specific version for all triggered runs.
    try:
        raw_train_version = ml_client.data.get(
            name=RAW_TRAIN_DATA_ASSET_NAME, label="latest"
        ).version
        raw_test_version = ml_client.data.get(
            name=RAW_TEST_DATA_ASSET_NAME, label="latest"
        ).version
        logger.info(
            f"Resolved data version '{raw_train_version}' for training asset "
            f"'{RAW_TRAIN_DATA_ASSET_NAME}' for the schedule."
        )
        logger.info(
            f"Resolved data version '{raw_test_version}' for test asset "
            f"'{RAW_TEST_DATA_ASSET_NAME}' for the schedule."
        )
    except Exception as e:
        logger.error(
            f"Failed to retrieve latest data asset versions for scheduling. "
            f"Please ensure that the data assets '{RAW_TRAIN_DATA_ASSET_NAME}' "
            f"and '{RAW_TEST_DATA_ASSET_NAME}' exist and have a 'latest' tag. "
            f"Error: {e}"
        )
        raise

    # Step 1: Get appropriate compute target
    compute_to_use = get_compute_for_job()

    # Create temporary code directory
    temp_dir = create_temp_code_directory()

    try:
        # Define Preprocessing Component
        preprocess_command = (
            "python -c \"import nltk; nltk.download('punkt', quiet=True); "
            "nltk.download('punkt_tab', quiet=True); "
            "nltk.download('wordnet', quiet=True); "
            "nltk.download('omw-1.4', quiet=True); "
            "nltk.download('averaged_perceptron_tagger', quiet=True); "
            "nltk.download('vader_lexicon', quiet=True); "
            "nltk.download('stopwords', quiet=True)\" "
            "&& python -m src.emotion_clf_pipeline.data "
            "--raw-train-path ${{inputs.raw_train_data}} "
            "--raw-test-path ${{inputs.raw_test_data}} "
            "--output-dir ${{outputs.processed_data}} "
            "--encoders-dir ${{outputs.encoders}} "
            f"--model-name-tokenizer {args.model_name_tokenizer} "
            f"--max-length {args.max_length} "
            f"--output-tasks {args.output_tasks}"
        )
        if args.register_data_assets:
            preprocess_command += " --register-data-assets"

        preprocess_component = CommandComponent(
            name="preprocess_data",
            display_name="DeBERTa Data Preprocessing Pipeline",
            description="Tokenizes and preprocesses raw text data.",
            inputs={
                "raw_train_data": Input(type=AssetTypes.URI_FOLDER),
                "raw_test_data": Input(type=AssetTypes.URI_FOLDER),
            },
            outputs={
                "processed_data": Output(type=AssetTypes.URI_FOLDER),
                "encoders": Output(type=AssetTypes.URI_FOLDER),
            },
            command=preprocess_command,
            environment=f"azureml:{ENV_NAME}:{ENV_VERSION}",
            code=temp_dir,
        )

        # Define Training Component
        train_command = (
            "python -c \"import nltk; nltk.download('punkt', quiet=True); "
            "nltk.download('punkt_tab', quiet=True); "
            "nltk.download('wordnet', quiet=True); "
            "nltk.download('omw-1.4', quiet=True); "
            "nltk.download('averaged_perceptron_tagger', quiet=True); "
            "nltk.download('vader_lexicon', quiet=True); "
            "nltk.download('stopwords', quiet=True)\" "
            "&& python -m src.emotion_clf_pipeline.train "
            "--train-data ${{inputs.processed_data}}/train.csv "
            "--test-data ${{inputs.processed_data}}/test.csv "
            "--encoders-dir ${{inputs.encoders}} "
            f"--model-name {args.model_name} "
            f"--batch-size {args.batch_size} "
            f"--learning-rate {args.learning_rate} "
            f"--epochs {args.epochs} "
            "--output-dir ${{outputs.trained_model}} "
            "# Cache-busting comment"
        )

        train_component = CommandComponent(
            name="train_emotion_classifier_v2",
            display_name="DeBERTa Training and Evaluation Pipeline",
            description="Trains a transformer model for emotion classification.",
            inputs={
                "processed_data": Input(type=AssetTypes.URI_FOLDER),
                "encoders": Input(type=AssetTypes.URI_FOLDER),
            },
            outputs={
                "trained_model": Output(type=AssetTypes.URI_FOLDER),
                "metrics_file": Output(type=AssetTypes.URI_FILE),
            },
            command=train_command,
            environment=f"azureml:{ENV_NAME}:{ENV_VERSION}",
            code=temp_dir,
        )

        # Define the pipeline
        pipeline_kwargs = {
            "description": "Scheduled end-to-end emotion classification training"
        }

        # Set compute configuration based on mode
        if COMPUTE_MODE == "serverless":
            # For serverless pipelines, use default_compute="serverless"
            pipeline_kwargs["default_compute"] = "serverless"
            logger.info("🎯 Scheduled pipeline configured for serverless compute")
        else:
            # For compute instances, use the compute target
            pipeline_kwargs["compute"] = compute_to_use
            logger.info(
                f"🎯 Scheduled pipeline configured for compute: " f"{compute_to_use}"
            )

        @dsl.pipeline(**pipeline_kwargs)
        def scheduled_emotion_clf_pipeline(
            raw_train_data: Input,
            raw_test_data: Input,
        ):
            preprocess_job = preprocess_component(
                raw_train_data=raw_train_data,
                raw_test_data=raw_test_data,
            )
            preprocess_job.display_name = "scheduled-preprocess-job"

            train_and_eval_job = train_component(
                processed_data=preprocess_job.outputs.processed_data,
                encoders=preprocess_job.outputs.encoders,
            )
            train_and_eval_job.display_name = "scheduled-train-and-eval-job"

            return {
                "pipeline_processed_data": preprocess_job.outputs.processed_data,
                "pipeline_trained_model": train_and_eval_job.outputs.trained_model,
            }

        # Instantiate the pipeline
        pipeline_job = scheduled_emotion_clf_pipeline(
            raw_train_data=Input(
                type=AssetTypes.URI_FOLDER,
                path=(f"azureml:{RAW_TRAIN_DATA_ASSET_NAME}:{raw_train_version}"),
            ),
            raw_test_data=Input(
                type=AssetTypes.URI_FOLDER,
                path=(f"azureml:{RAW_TEST_DATA_ASSET_NAME}:{raw_test_version}"),
            ),
        )

        # Configure serverless resources if needed
        if COMPUTE_MODE == "serverless":
            config = ACTIVE_COMPUTE_CONFIG
            # Set resources for the scheduled pipeline
            pipeline_job.settings.default_datastore = None
            pipeline_job.settings.default_compute = "serverless"
            logger.info(
                f"🎯 Configured scheduled pipeline for serverless with VM size: "
                f"{config['vm_size']}"
            )

        # Set pipeline properties
        pipeline_job.display_name = f"{args.pipeline_name}"
        pipeline_job.experiment_name = "emotion-clf-deberta-architecture"

        return pipeline_job

    finally:
        # Note: Don't cleanup temp_dir here as it's needed for the schedule
        pass


def list_pipeline_schedules() -> list:
    """
    List all pipeline schedules in the Azure ML workspace.

    Returns:
        List of schedule information dictionaries
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure ML SDK not available")
        return []

    try:
        ml_client = get_ml_client()
        schedules = list(ml_client.schedules.list())

        schedule_info = []
        for schedule in schedules:
            created_time = None
            if schedule.creation_context:
                created_time = schedule.creation_context.created_at

            info = {
                "name": schedule.name,
                "enabled": schedule.is_enabled,
                "description": schedule.description,
                "trigger_type": type(schedule.trigger).__name__,
                "created_time": created_time,
                "tags": schedule.tags,
            }

            # Add trigger-specific information
            if hasattr(schedule.trigger, "expression"):
                info["cron_expression"] = schedule.trigger.expression
                info["timezone"] = schedule.trigger.time_zone
            elif hasattr(schedule.trigger, "frequency"):
                info["frequency"] = schedule.trigger.frequency
                info["interval"] = schedule.trigger.interval

            schedule_info.append(info)

        logger.info(f"Found {len(schedule_info)} pipeline schedules")
        return schedule_info

    except Exception as e:
        logger.error(f"Failed to list pipeline schedules: {e}")
        return []


def get_schedule_details(schedule_name: str) -> Optional[Dict]:
    """
    Get detailed information about a specific schedule.

    Args:
        schedule_name: Name of the schedule

    Returns:
        Dictionary with schedule details or None if not found
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure ML SDK not available")
        return None

    try:
        ml_client = get_ml_client()
        schedule = ml_client.schedules.get(schedule_name)
        created_time = None
        if schedule.creation_context:
            created_time = schedule.creation_context.created_at
        last_modified = None
        if schedule.creation_context:
            last_modified = schedule.creation_context.last_modified_at
        compute = None
        if hasattr(schedule.create_job, "compute"):
            compute = schedule.create_job.compute

        details = {
            "name": schedule.name,
            "enabled": schedule.is_enabled,
            "description": schedule.description,
            "trigger_type": type(schedule.trigger).__name__,
            "created_time": created_time,
            "last_modified": last_modified,
            "tags": schedule.tags,
            "create_job": {
                "name": schedule.create_job.display_name,
                "experiment": schedule.create_job.experiment_name,
                "compute": compute,
            },
        }

        # Add trigger-specific information
        if hasattr(schedule.trigger, "expression"):
            details["cron_expression"] = schedule.trigger.expression
            details["timezone"] = schedule.trigger.time_zone
        elif hasattr(schedule.trigger, "frequency"):
            details["frequency"] = schedule.trigger.frequency
            details["interval"] = schedule.trigger.interval

        return details

    except Exception as e:
        logger.error(f"Failed to get schedule details for '{schedule_name}': {e}")
        return None


def enable_schedule(schedule_name: str) -> bool:
    """
    Enable a pipeline schedule.

    Args:
        schedule_name: Name of the schedule to enable

    Returns:
        True if successful, False otherwise
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure ML SDK not available")
        return False

    try:
        ml_client = get_ml_client()

        # Get the existing schedule
        schedule = ml_client.schedules.get(schedule_name)
        schedule.is_enabled = True

        # Update the schedule
        ml_client.schedules.begin_create_or_update(schedule)

        logger.info(f"✅ Enabled schedule '{schedule_name}'")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to enable schedule '{schedule_name}': {e}")
        return False


def disable_schedule(schedule_name: str) -> bool:
    """
    Disable a pipeline schedule.

    Args:
        schedule_name: Name of the schedule to disable

    Returns:
        True if successful, False otherwise
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure ML SDK not available")
        return False

    try:
        ml_client = get_ml_client()

        # Get the existing schedule
        schedule = ml_client.schedules.get(schedule_name)
        schedule.is_enabled = False

        # Update the schedule
        ml_client.schedules.begin_create_or_update(schedule)

        logger.info(f"🔒 Disabled schedule '{schedule_name}'")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to disable schedule '{schedule_name}': {e}")
        return False


def delete_schedule(schedule_name: str) -> bool:
    """
    Delete a pipeline schedule.

    Args:
        schedule_name: Name of the schedule to delete

    Returns:
        True if successful, False otherwise
    """
    if not AZURE_AVAILABLE:
        logger.error("Azure ML SDK not available")
        return False

    try:
        ml_client = get_ml_client()
        ml_client.schedules.begin_delete(schedule_name)

        logger.info(f"🗑️ Deleted schedule '{schedule_name}'")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to delete schedule '{schedule_name}': {e}")
        return False


def create_daily_schedule(
    pipeline_name: str,
    hour: int = 0,
    minute: int = 0,
    timezone: str = "UTC",
    enabled: bool = True,
) -> Optional[str]:
    """
    Create a daily schedule for the pipeline.

    Args:
        pipeline_name: Name of the pipeline
        hour: Hour of day (0-23, default: 0 for midnight)
        minute: Minute of hour (0-59, default: 0)
        timezone: Timezone (default: UTC)
        enabled: Whether schedule should be enabled

    Returns:
        Schedule ID if successful, None otherwise
    """
    cron_expression = f"{minute} {hour} * * *"
    schedule_name = f"{pipeline_name}-daily-{hour:02d}{minute:02d}"
    description = f"Daily execution of {pipeline_name} at \
        {hour:02d}:{minute:02d} {timezone}"

    return create_pipeline_schedule(
        pipeline_name=pipeline_name,
        schedule_name=schedule_name,
        cron_expression=cron_expression,
        timezone=timezone,
        description=description,
        enabled=enabled,
    )


def create_weekly_schedule(
    pipeline_name: str,
    day_of_week: int = 0,  # 0=Sunday, 1=Monday, etc.
    hour: int = 0,
    minute: int = 0,
    timezone: str = "UTC",
    enabled: bool = True,
) -> Optional[str]:
    """
    Create a weekly schedule for the pipeline.

    Args:
        pipeline_name: Name of the pipeline
        day_of_week: Day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
        hour: Hour of day (0-23, default: 0 for midnight)
        minute: Minute of hour (0-59, default: 0)
        timezone: Timezone (default: UTC)
        enabled: Whether schedule should be enabled

    Returns:
        Schedule ID if successful, None otherwise
    """
    days = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    cron_expression = f"{minute} {hour} * * {day_of_week}"
    schedule_name = f"{pipeline_name}-weekly-{days[day_of_week].lower()}\
        -{hour:02d}{minute:02d}"
    description = f"Weekly execution of {pipeline_name} on {days[day_of_week]} \
        at {hour:02d}:{minute:02d} {timezone}"

    return create_pipeline_schedule(
        pipeline_name=pipeline_name,
        schedule_name=schedule_name,
        cron_expression=cron_expression,
        timezone=timezone,
        description=description,
        enabled=enabled,
    )


def create_monthly_schedule(
    pipeline_name: str,
    day_of_month: int = 1,
    hour: int = 0,
    minute: int = 0,
    timezone: str = "UTC",
    enabled: bool = True,
) -> Optional[str]:
    """
    Create a monthly schedule for the pipeline.

    Args:
        pipeline_name: Name of the pipeline
        day_of_month: Day of month (1-31)
        hour: Hour of day (0-23, default: 0 for midnight)
        minute: Minute of hour (0-59, default: 0)
        timezone: Timezone (default: UTC)
        enabled: Whether schedule should be enabled

    Returns:
        Schedule ID if successful, None otherwise
    """
    cron_expression = f"{minute} {hour} {day_of_month} * *"
    schedule_name = f"{pipeline_name}-monthly-{day_of_month:02d}-{hour:02d}{minute:02d}"
    description = f"Monthly execution of {pipeline_name} on day {day_of_month} \
        at {hour:02d}:{minute:02d} {timezone}"

    return create_pipeline_schedule(
        pipeline_name=pipeline_name,
        schedule_name=schedule_name,
        cron_expression=cron_expression,
        timezone=timezone,
        description=description,
        enabled=enabled,
    )


def print_schedule_summary():
    """Print a formatted summary of all pipeline schedules."""
    schedules = list_pipeline_schedules()

    if not schedules:
        print("📅 No pipeline schedules found.")
        return

    print(f"📅 Pipeline Schedules ({len(schedules)} total)")
    print("=" * 70)

    for schedule in schedules:
        status_icon = "🟢" if schedule.get("enabled", False) else "🔴"
        print(f"{status_icon} {schedule['name']}")

        if schedule.get("cron_expression"):
            print(
                f"   ⏰ Cron: {schedule['cron_expression']} \
                ({schedule.get('timezone', 'UTC')})"
            )
        elif schedule.get("frequency"):
            print(
                f"   🔄 Every {schedule.get('interval', 1)} \
                {schedule.get('frequency', 'unknown')}"
            )

        if schedule.get("description"):
            print(f"   📝 {schedule['description']}")

        if schedule.get("created_time"):
            print(f"   📅 Created: {schedule['created_time']}")

        print()


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================


def setup_default_schedules(
    pipeline_name: str = "deberta-full-pipeline",
) -> Dict[str, Optional[str]]:
    """
    Set up common scheduling patterns for the emotion classification pipeline.

    Args:
        pipeline_name: Name of the pipeline to schedule

    Returns:
        Dictionary with schedule types and their IDs
    """
    results = {}

    logger.info(f"🕐 Setting up default schedules for '{pipeline_name}'...")

    # Daily at midnight UTC
    results["daily_midnight"] = create_daily_schedule(
        pipeline_name=pipeline_name,
        hour=0,
        minute=0,
        timezone="UTC",
        enabled=False,  # Start disabled, user can enable when ready
    )

    # Weekly on Sunday at midnight UTC
    results["weekly_sunday"] = create_weekly_schedule(
        pipeline_name=pipeline_name,
        day_of_week=0,  # Sunday
        hour=0,
        minute=0,
        timezone="UTC",
        enabled=False,
    )

    # Monthly on the 1st at midnight UTC
    results["monthly_first"] = create_monthly_schedule(
        pipeline_name=pipeline_name,
        day_of_month=1,
        hour=0,
        minute=0,
        timezone="UTC",
        enabled=False,
    )

    successful_schedules = [k for k, v in results.items() if v is not None]
    failed_schedules = [k for k, v in results.items() if v is None]

    logger.info(
        f"✅ Created {len(successful_schedules)} \
        schedules: {', '.join(successful_schedules)}"
    )
    if failed_schedules:
        logger.warning(
            f"❌ Failed to create {len(failed_schedules)} \
            schedules: {', '.join(failed_schedules)}"
        )

    return results
