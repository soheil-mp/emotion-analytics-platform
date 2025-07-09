"""
Enhanced Command-Line Interface for the Emotion Classification Pipeline.

This script provides a unified CLI for both local and Azure ML execution of:
- Data preprocessing pipeline
- Model training pipeline
- Prediction from YouTube URLs
- Pipeline status monitoring

Supports seamless switching between local and Azure ML execution modes
while maintaining backward compatibility with existing usage patterns.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import traceback

import pandas as pd
from transformers import AutoTokenizer

# Azure ML SDK v2 imports
try:
    from . import azure_pipeline
    from .azure_endpoint import AzureMLKubernetesDeployer
    from .azure_pipeline import (
        register_processed_data_assets,
        submit_preprocess_pipeline,
        submit_training_pipeline,
    )
    from .data import DataPreparation, DatasetLoader

    # from .predict import process_youtube_url_and_predict
except ImportError:
    import azure_pipeline
    from azure_endpoint import AzureMLKubernetesDeployer
    from azure_pipeline import (
        register_processed_data_assets,
        submit_preprocess_pipeline,
        submit_training_pipeline,
    )

    # from predict import process_youtube_url_and_predict
    from data import DataPreparation, DatasetLoader


# A simple retry decorator
def retry(tries=3, delay=5, backoff=2):
    """
    A simple retry decorator for functions that might fail due to transient issues.

    Args:
        tries (int): The maximum number of attempts.
        delay (int): The initial delay between retries in seconds.
        backoff (int): The factor by which the delay should increase for each retry.
    """

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    # Check for specific, recoverable network errors
                    if (
                        "ConnectionResetError" in str(e)
                        or "Connection aborted" in str(e)
                        or "10054" in str(e)
                    ):
                        msg = f"Retrying in {mdelay} seconds due to network error: {e}"
                        logger.warning(msg)
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    else:
                        # If it's not a network error, fail fast
                        raise
            # Final attempt
            return f(*args, **kwargs)

        return f_retry

    return deco_retry


# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


def add_preprocess_args(parser):
    """Add preprocessing-specific arguments."""
    parser.add_argument(
        "--raw-train-path",
        type=str,
        default="data/raw/train",
        help="Path to raw training data (directory or CSV file)",
    )

    parser.add_argument(
        "--raw-test-path",
        type=str,
        default="data/raw/test/test_data-0001.csv",
        help="Path to raw test data CSV file",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for processed data",
    )

    parser.add_argument(
        "--encoders-dir",
        type=str,
        default="models/encoders",
        help="Directory to save label encoders",
    )

    parser.add_argument(
        "--model-name-tokenizer",
        type=str,
        default="microsoft/deberta-v3-xsmall",
        help="HuggingFace model name for tokenizer",
    )

    parser.add_argument(
        "--max-length",
        type=int,
        default=256,
        help="Maximum sequence length for tokenization",
    )

    parser.add_argument(
        "--output-tasks",
        type=str,
        default="emotion,sub-emotion,intensity",
        help="Comma-separated list of output tasks",
    )

    parser.add_argument(
        "--register-data-assets",
        action="store_true",
        default=True,
        help="Register processed data as Azure ML data assets after completion",
    )

    parser.add_argument(
        "--no-register-data-assets",
        action="store_false",
        dest="register_data_assets",
        help="Skip registering processed data as Azure ML data assets",
    )


def add_train_args(parser):
    """Add training-specific arguments."""
    parser.add_argument(
        "--processed-train-dir",
        type=str,
        default="data/processed",
        help="Directory containing processed training data",
    )

    parser.add_argument(
        "--processed-test-dir",
        type=str,
        default="data/processed",
        help="Directory containing processed test data",
    )

    parser.add_argument(
        "--encoders-dir",
        type=str,
        default="models/encoders",
        help="Directory containing label encoders",
    )

    parser.add_argument(
        "--model-name",
        type=str,
        default="microsoft/deberta-v3-xsmall",
        help="HuggingFace transformer model name",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for training and evaluation",
    )

    parser.add_argument(
        "--learning-rate", type=float, default=2e-5, help="Learning rate for optimizer"
    )

    parser.add_argument(
        "--epochs", type=int, default=1, help="Number of training epochs"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/weights",
        help="Output directory for trained model weights",
    )

    parser.add_argument(
        "--metrics-file",
        type=str,
        default="models/evaluation/metrics.json",
        help="Output file for training metrics",
    )

    parser.add_argument(
        "--output-tasks",
        type=str,
        default="emotion,sub-emotion,intensity",
        help="Comma-separated list of output tasks",
    )


def add_pipeline_args(parser):
    """Add arguments for the complete training pipeline."""
    # --- Arguments from add_preprocess_args ---
    parser.add_argument(
        "--raw-train-path",
        type=str,
        default="data/raw/train",
        help="Path to raw training data (directory or CSV file) for the pipeline.",
    )
    parser.add_argument(
        "--raw-test-path",
        type=str,
        default="data/raw/test/test_data-0001.csv",
        help="Path to raw test data CSV file for the pipeline.",
    )
    parser.add_argument(
        "--model-name-tokenizer",
        type=str,
        default="microsoft/deberta-v3-xsmall",
        help="HuggingFace model name for the tokenizer.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=256,
        help="Maximum sequence length for tokenization.",
    )
    # parser.add_argument(
    #     "--output-tasks",
    #     type=str,
    #     default="emotion,sub_emotion,intensity",
    #     help="Comma-separated list of output tasks."
    # )
    parser.add_argument(
        "--register-data-assets",
        action="store_true",
        default=True,
        help="Register processed data as Azure ML data assets.",
    )

    parser.add_argument(
        "--no-register-data-assets",
        action="store_false",
        dest="register_data_assets",
        help="Skip registering processed data as Azure ML data assets",
    )

    # --- Arguments from add_train_args ---
    parser.add_argument(
        "--model-name",
        type=str,
        default="microsoft/deberta-v3-xsmall",
        help="HuggingFace transformer model name.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for training and evaluation.",
    )
    parser.add_argument(
        "--learning-rate", type=float, default=2e-5, help="Learning rate for optimizer."
    )
    parser.add_argument(
        "--epochs", type=int, default=1, help="Number of training epochs."
    )
    parser.add_argument(
        "--metrics-file",
        type=str,
        default="models/evaluation/metrics.json",
        help="Output file for training metrics.",
    )

    # --- Shared/Conflicting Arguments (handled once) ---
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/weights",
        help="Output directory for final trained model weights.",
    )
    parser.add_argument(
        "--encoders-dir",
        type=str,
        default="models/encoders",
        help="Directory for label encoders (output from preprocess, input to train).",
    )
    parser.add_argument(
        "--output-tasks",
        type=str,
        default="emotion,sub-emotion,intensity",
        help="Comma-separated list of output tasks for the pipeline.",
    )

    # --- Pipeline-specific arguments ---
    parser.add_argument(
        "--pipeline-name",
        type=str,
        default="deberta-full-pipeline",
        help="Base name for the Azure ML pipeline",
    )

    parser.add_argument(
        "--registration-f1-threshold",
        type=float,
        default=0.10,
        help="Minimum F1 score for model registration in Azure ML",
    )


def add_schedule_pipeline_args(parser):
    """Add pipeline-specific arguments for scheduling (avoiding conflicts)."""
    parser.add_argument(
        "--pipeline-name",
        type=str,
        default="scheduled-deberta-training-pipeline",
        help="Name of the Azure ML pipeline",
    )

    parser.add_argument(
        "--data-path",
        type=str,
        default="./data/processed",
        help="Path to processed training data directory",
    )

    parser.add_argument(
        "--output-path",
        type=str,
        default="./models",
        help="Path to output trained models",
    )

    parser.add_argument(
        "--experiment-name",
        type=str,
        default="scheduled-deberta-training-experiment",
        help="Name of the Azure ML experiment",
    )

    parser.add_argument(
        "--compute-target",
        type=str,
        default="cpu-cluster",
        help="Azure ML compute target name",
    )


def add_predict_args(parser):
    """Add prediction-specific arguments."""
    parser.add_argument("url", type=str, help="YouTube URL to analyze")

    parser.add_argument(
        "--transcription-method",
        type=str,
        choices=["whisper", "assemblyai"],
        default="whisper",
        help="Transcription method to use",
    )

    parser.add_argument(
        "--output-file", type=str, help="Output file path for results (JSON format)"
    )


def run_preprocess_local(args):
    """Run data preprocessing locally."""
    logger.info("Running data preprocessing locally...")

    try:

        # Parse output tasks
        output_tasks = [task.strip() for task in args.output_tasks.split(",")]

        # Load raw data
        dataset_loader = DatasetLoader()

        if os.path.isdir(args.raw_train_path):
            train_df = dataset_loader.load_training_data(args.raw_train_path)
        else:
            train_df = pd.read_csv(args.raw_train_path)
            # Handle column name consistency - convert hyphen to underscore
            if "sub-emotion" in train_df.columns:
                train_df = train_df.rename(columns={"sub-emotion": "sub_emotion"})

        test_df = dataset_loader.load_test_data(args.raw_test_path)

        logger.info(
            f"Loaded {len(train_df)} training samples and {len(test_df)} test samples"
        )

        # Clean data by removing rows with NaN in critical columns
        critical_columns = ["text", "emotion", "sub-emotion", "intensity"]
        # Only check columns that exist in the dataframes
        train_critical = [col for col in critical_columns if col in train_df.columns]
        test_critical = [col for col in critical_columns if col in test_df.columns]

        initial_train_len = len(train_df)
        initial_test_len = len(test_df)

        train_df = train_df.dropna(subset=train_critical)
        test_df = test_df.dropna(subset=test_critical)

        # Rename sub-emotion column to sub_emotion for consistency with training code
        if "sub-emotion" in train_df.columns:
            train_df = train_df.rename(columns={"sub-emotion": "sub_emotion"})
        if "sub-emotion" in test_df.columns:
            test_df = test_df.rename(columns={"sub-emotion": "sub_emotion"})

        # Update output_tasks to use underscore instead of hyphen
        output_tasks = [
            task.replace("sub-emotion", "sub_emotion") for task in output_tasks
        ]

        train_removed = initial_train_len - len(train_df)
        test_removed = initial_test_len - len(test_df)
        logger.info(
            f"After cleaning: {len(train_df)} training samples "
            f"({train_removed} removed)"
        )
        logger.info(
            f"After cleaning: {len(test_df)} test samples " f"({test_removed} removed)"
        )

        # Apply intensity mapping
        intensity_mapping = {
            "mild": "mild",
            "neutral": "mild",
            "moderate": "moderate",
            "intense": "strong",
            "overwhelming": "strong",
        }
        train_df["intensity"] = (
            train_df["intensity"].map(intensity_mapping).fillna("mild")
        )
        test_df["intensity"] = (
            test_df["intensity"].map(intensity_mapping).fillna("mild")
        )

        # Initialize tokenizer and data preparation
        tokenizer = AutoTokenizer.from_pretrained(args.model_name_tokenizer)

        feature_config = {
            "pos": False,
            "textblob": False,
            "vader": False,
            "tfidf": True,
            "emolex": True,
        }

        data_prep = DataPreparation(
            output_columns=output_tasks,
            tokenizer=tokenizer,
            max_length=args.max_length,
            batch_size=16,  # Not used in preprocessing
            feature_config=feature_config,
            encoders_save_dir=args.encoders_dir,
        )

        # Create output directories
        os.makedirs(args.output_dir, exist_ok=True)
        os.makedirs(args.encoders_dir, exist_ok=True)

        # Prepare data (this will save encoders and process data)
        train_dataloader, val_dataloader, test_dataloader = data_prep.prepare_data(
            train_df=train_df, test_df=test_df, validation_split=0.1
        )

        # Save processed data
        train_output_path = os.path.join(args.output_dir, "train.csv")
        test_output_path = os.path.join(args.output_dir, "test.csv")

        data_prep.train_df_processed.to_csv(train_output_path, index=False)
        data_prep.test_df_processed.to_csv(test_output_path, index=False)

        logger.info("Preprocessing completed successfully!")
        logger.info(f"Processed data saved to: {args.output_dir}")
        logger.info(f"Encoders saved to: {args.encoders_dir}")

    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise


def run_preprocess_azure(args):
    """Run data preprocessing on Azure ML."""
    logger.info("Submitting data preprocessing pipeline to Azure ML...")

    try:
        # Submit Azure ML pipeline
        job = submit_preprocess_pipeline(args)
        logger.info(f"Azure ML preprocessing job submitted: {job.name}")
        logger.info(f"Monitor at: {job.studio_url}")

        # Check if we should register data assets after completion
        if getattr(args, "register_data_assets", True):
            logger.info("Waiting for job completion to register data assets...")
            register_processed_data_assets(job)

    except ImportError:
        logger.error("Azure ML dependencies not available. Please install azure-ai-ml")
        raise
    except Exception as e:
        logger.error(f"Azure ML preprocessing submission failed: {str(e)}")
        raise


def run_train_local(args):
    """Run model training locally."""
    logger.info("Running model training locally...")

    try:
        # Build command to run train.py as a module
        # Only pass arguments that train.py actually supports
        cmd = [
            sys.executable,
            "-m",
            "src.emotion_clf_pipeline.train",
            "--model-name",
            args.model_name,
            "--batch-size",
            str(args.batch_size),
            "--learning-rate",
            str(args.learning_rate),
            "--epochs",
            str(args.epochs),
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

        # Run the training script
        result = subprocess.run(cmd, check=True, capture_output=False)

        if result.returncode == 0:
            logger.info("Local training completed successfully!")
        else:
            raise subprocess.CalledProcessError(result.returncode, cmd)

    except subprocess.CalledProcessError as e:
        logger.error(f"Training process failed with return code {e.returncode}")
        raise
    except Exception as e:
        logger.error(f"Local training failed: {str(e)}")
        raise


def run_train_azure(args):
    """Run model training on Azure ML."""
    logger.info("Submitting model training pipeline to Azure ML...")

    try:
        # Submit Azure ML pipeline
        job = submit_training_pipeline(args)
        logger.info(f"Azure ML training job submitted: {job.name}")
        logger.info(f"Monitor at: {job.studio_url}")

    except ImportError:
        logger.error("Azure ML dependencies not available. Please install azure-ai-ml")
        raise
    except Exception as e:
        logger.error(f"Azure ML training submission failed: {str(e)}")
        raise


def cmd_predict(args):
    """Handle predict command with support for both local and Azure inference."""
    import json
    from pathlib import Path

    # Import prediction functions
    try:
        from .predict import predict_emotions_azure, predict_emotions_local
    except ImportError:
        from emotion_clf_pipeline.predict import (
            predict_emotions_azure,
            predict_emotions_local,
        )

    logger.info("🎬 Starting emotion prediction pipeline...")

    try:
        # Determine prediction mode
        if args.use_azure:
            logger.info("🌐 Using Azure ML endpoint for prediction")

            # Run Azure prediction (auto-loads config from .env with CLI overrides)
            result = predict_emotions_azure(
                video_url=args.input,
                endpoint_url=args.azure_endpoint,  # Optional - uses .env
                api_key=args.azure_api_key,  # Optional - uses .env
                use_stt=args.use_stt,
                chunk_size=args.chunk_size,
                use_ngrok=args.use_ngrok,  # Optional - uses .env
                server_ip=args.server_ip,  # Optional - uses .env
            )
        else:
            logger.info("🖥️ Using local model for prediction")

            # Run local prediction
            result = predict_emotions_local(
                video_url=args.input,
                model_path=args.model_path,
                config_path=args.config_path,
                use_stt=args.use_stt,
                chunk_size=args.chunk_size,
            )

        # Save results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Results saved to: {output_path}")

        # Display summary
        display_prediction_summary(result)

        logger.info("✅ Emotion prediction completed successfully!")

    except Exception as e:
        logger.error(f"❌ Prediction failed: {e}")
        raise SystemExit(1)


def display_prediction_summary(result: dict):
    """Display a summary of the prediction results."""
    print("\n" + "=" * 60)
    print("🎭 EMOTION PREDICTION SUMMARY")
    print("=" * 60)

    metadata = result.get("metadata", {})
    predictions = result.get("predictions", [])

    # Basic info
    print(f"📺 Video/Audio: {metadata.get('video_url', 'N/A')}")
    print(f"🧠 Model Type: {metadata.get('model_type', 'N/A').title()}")
    print(f"📄 Transcript Length: {metadata.get('transcript_length', 0)} characters")
    print(f"📦 Chunks Processed: {len(predictions)}")

    if metadata.get("model_type") == "azure":
        print(f"🌐 Endpoint: {metadata.get('endpoint_url', 'N/A')}")
        if metadata.get("ngrok_used"):
            print("🔄 NGROK tunnel used")

    print(f"🎤 STT Used: {'Yes' if metadata.get('stt_used') else 'No'}")

    # Prediction summary
    if predictions:
        successful_chunks = sum(1 for p in predictions if p.get("status") == "success")
        failed_chunks = len(predictions) - successful_chunks

        print("\n📊 Processing Results:")
        print(f"   ✅ Successful: {successful_chunks}")
        if failed_chunks > 0:
            print(f"   ❌ Failed: {failed_chunks}")

        # Show first successful prediction as example
        for pred in predictions:
            if pred.get("status") == "success":
                if metadata.get("model_type") == "azure":
                    # Azure predictions
                    decoded = pred.get("decoded_predictions", {})
                    if decoded:
                        print(
                            "\n🎭 Sample Prediction ",
                            f"(Chunk {pred.get('chunk_index', 0) + 1}):",
                        )
                        print(f"   😊 Emotion: {decoded.get('emotion', 'N/A')}")
                        print(f"   💝 Sub-emotion: {decoded.get('sub_emotion', 'N/A')}")
                        print(f"   📊 Intensity: {decoded.get('intensity', 'N/A')}")

                        # Show confidence scores if available
                        if "emotion_confidence" in decoded:
                            print(
                                "   🎯 Confidence: "
                                f"{decoded.get('emotion_confidence', 0):.3f}"
                            )
                else:
                    # Local predictions
                    chunk_preds = pred.get("predictions", {})
                    if chunk_preds:
                        print(
                            "\n🎭 Sample Prediction ",
                            f"(Chunk {pred.get('chunk_index', 0) + 1}):",
                        )
                        print(f"   📝 Text: {pred.get('chunk_text', 'N/A')}")
                        print(
                            "   📊 Raw predictions available ",
                            "(use --output to save full results)",
                        )
                break

    print("=" * 60)


def cmd_data(args):
    """Handle data preprocessing commands."""
    print("📊 Data preprocessing commands not yet implemented in this version.")


def cmd_endpoint(args):
    """Handle endpoint management commands."""
    if args.endpoint_command == "deploy":
        cmd_endpoint_deploy(args)
    elif args.endpoint_command == "test":
        cmd_endpoint_test(args)
    elif args.endpoint_command == "details":
        cmd_endpoint_details(args)
    elif args.endpoint_command == "cleanup":
        cmd_endpoint_cleanup(args)
    else:
        print("Available endpoint commands: deploy, test, details, cleanup")


def run_pipeline_local(args):
    """Run the complete pipeline locally (preprocess + train)."""
    logger.info("Starting complete local pipeline: preprocess + train")

    try:
        # Step 1: Run preprocessing
        logger.info("=" * 60)
        logger.info("STEP 1: DATA PREPROCESSING")
        logger.info("=" * 60)
        run_preprocess_local(args)

        # Step 2: Run training
        logger.info("=" * 60)
        logger.info("STEP 2: MODEL TRAINING")
        logger.info("=" * 60)
        run_train_local(args)

        logger.info("=" * 60)
        logger.info("COMPLETE PIPELINE FINISHED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise


@retry(tries=3, delay=10, backoff=2)
def run_pipeline_azure(args):
    """Run the complete pipeline on Azure ML."""
    logger.info("🚀 Submitting complete pipeline to Azure ML...")
    try:
        job = azure_pipeline.submit_complete_pipeline(args)
        logger.info(f"✅ Pipeline submitted successfully. Job ID: {job.name}")
        logger.info(f"➡️  Monitor job at: {job.studio_url}")

    except Exception as e:
        logger.error(f"❌ Pipeline submission failed: {str(e)}", exc_info=True)
        sys.exit(1)


def cmd_preprocess(args):
    """Handle preprocess command."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine execution mode
    mode = "azure" if args.azure else args.mode

    if mode == "local":
        run_preprocess_local(args)
    elif mode == "azure":
        run_preprocess_azure(args)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def cmd_train(args):
    """Handle train command."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine execution mode
    mode = "azure" if args.azure else args.mode

    if mode == "local":
        run_train_local(args)
    elif mode == "azure":
        run_train_azure(args)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def cmd_status(args):
    """Check the status of an Azure ML job."""
    logger.info(f"Checking status of job: {args.job_id}")
    status = azure_pipeline.get_pipeline_status(args.job_id)
    logger.info(f"Job status: {status}")


def cmd_pipeline(args):
    """Execute the appropriate pipeline based on mode."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.azure:
        run_pipeline_azure(args)
    else:
        run_pipeline_local(args)


def add_schedule_create_args(parser):
    """Add arguments for creating pipeline schedules."""
    parser.add_argument(
        "--schedule-name", type=str, required=True, help="Name for the schedule"
    )

    parser.add_argument(
        "--cron",
        type=str,
        help="Cron expression (e.g., '0 0 * * *' for daily at midnight)",
    )

    parser.add_argument(
        "--daily",
        action="store_true",
        help="Create daily schedule (use with --hour and --minute)",
    )

    parser.add_argument(
        "--weekly",
        type=int,
        metavar="DAY",
        help="Create weekly schedule on specified day (0=Sunday, 1=Monday, etc.)",
    )

    parser.add_argument(
        "--monthly",
        type=int,
        metavar="DAY",
        help="Create monthly schedule on specified day (1-31)",
    )

    parser.add_argument(
        "--hour", type=int, default=0, help="Hour of day (0-23, default: 0)"
    )

    parser.add_argument(
        "--minute", type=int, default=0, help="Minute of hour (0-59, default: 0)"
    )

    parser.add_argument(
        "--timezone",
        type=str,
        default="UTC",
        help="Timezone for the schedule (default: UTC)",
    )

    parser.add_argument("--description", type=str, help="Description for the schedule")

    parser.add_argument(
        "--enabled",
        action="store_true",
        default=False,
        help="Enable the schedule immediately (default: disabled)",
    )

    # Add pipeline configuration arguments
    add_schedule_pipeline_args(parser)


def cmd_schedule_create(args):
    """Handle schedule create command."""
    try:
        # Determine schedule type and create accordingly
        if args.cron:
            schedule_id = azure_pipeline.create_pipeline_schedule(
                pipeline_name=args.pipeline_name,
                schedule_name=args.schedule_name,
                cron_expression=args.cron,
                timezone=args.timezone,
                description=args.description,
                enabled=args.enabled,
                args=args,
            )
        elif args.daily:
            schedule_id = azure_pipeline.create_daily_schedule(
                pipeline_name=args.pipeline_name,
                hour=args.hour,
                minute=args.minute,
                timezone=args.timezone,
                enabled=args.enabled,
            )
        elif args.weekly is not None:
            schedule_id = azure_pipeline.create_weekly_schedule(
                pipeline_name=args.pipeline_name,
                day_of_week=args.weekly,
                hour=args.hour,
                minute=args.minute,
                timezone=args.timezone,
                enabled=args.enabled,
            )
        elif args.monthly is not None:
            schedule_id = azure_pipeline.create_monthly_schedule(
                pipeline_name=args.pipeline_name,
                day_of_month=args.monthly,
                hour=args.hour,
                minute=args.minute,
                timezone=args.timezone,
                enabled=args.enabled,
            )
        else:
            logger.error(
                "Please specify one of: --cron, --daily, --weekly, or --monthly"
            )
            return

        if schedule_id:
            logger.info(f"✅ Successfully created schedule: {schedule_id}")
        else:
            logger.error("❌ Failed to create schedule")

    except Exception as e:
        logger.error(f"❌ Schedule creation failed: {e}")


def cmd_schedule_list(args):
    """Handle schedule list command."""
    try:
        azure_pipeline.print_schedule_summary()

    except Exception as e:
        logger.error(f"❌ Failed to list schedules: {e}")


def cmd_schedule_details(args):
    """Handle schedule details command."""
    try:
        details = azure_pipeline.get_schedule_details(args.schedule_name)

        if details:
            print(f"📅 Schedule Details: {args.schedule_name}")
            print("=" * 50)
            print(f"Enabled: {'🟢 Yes' if details.get('enabled') else '🔴 No'}")
            print(f"Description: {details.get('description', 'N/A')}")
            print(f"Trigger Type: {details.get('trigger_type', 'Unknown')}")

            if details.get("cron_expression"):
                print(f"Cron Expression: {details['cron_expression']}")
                print(f"Timezone: {details.get('timezone', 'UTC')}")
            elif details.get("frequency"):
                print(
                    f"Frequency: Every {details.get('interval', 1)} \
                    {details.get('frequency')}"
                )

            if details.get("created_time"):
                print(f"Created: {details['created_time']}")
            if details.get("last_modified"):
                print(f"Modified: {details['last_modified']}")

            if details.get("create_job"):
                job_info = details["create_job"]
                print(f"Pipeline: {job_info.get('name', 'N/A')}")
                print(f"Experiment: {job_info.get('experiment', 'N/A')}")
                if job_info.get("compute"):
                    print(f"Compute: {job_info['compute']}")

            if details.get("tags"):
                print("Tags:")
                for key, value in details["tags"].items():
                    print(f"  {key}: {value}")
        else:
            logger.error(f"❌ Schedule '{args.schedule_name}' not found")

    except Exception as e:
        logger.error(f"❌ Failed to get schedule details: {e}")


def cmd_schedule_enable(args):
    """Handle schedule enable command."""
    try:
        if azure_pipeline.enable_schedule(args.schedule_name):
            logger.info(f"✅ Schedule '{args.schedule_name}' enabled successfully")
        else:
            logger.error(f"❌ Failed to enable schedule '{args.schedule_name}'")

    except Exception as e:
        logger.error(f"❌ Failed to enable schedule: {e}")


def cmd_schedule_disable(args):
    """Handle schedule disable command."""
    try:
        if azure_pipeline.disable_schedule(args.schedule_name):
            logger.info(f"✅ Schedule '{args.schedule_name}' disabled successfully")
        else:
            logger.error(f"❌ Failed to disable schedule '{args.schedule_name}'")

    except Exception as e:
        logger.error(f"❌ Failed to disable schedule: {e}")


def cmd_schedule_delete(args):
    """Handle schedule delete command."""
    try:
        # Confirm deletion unless --confirm is used
        if not args.confirm:
            response = input(
                f"Are you sure you want to delete schedule \
                '{args.schedule_name}'? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                logger.info("❌ Deletion cancelled")
                return

        if azure_pipeline.delete_schedule(args.schedule_name):
            logger.info(f"✅ Schedule '{args.schedule_name}' deleted successfully")
        else:
            logger.error(f"❌ Failed to delete schedule '{args.schedule_name}'")

    except Exception as e:
        logger.error(f"❌ Failed to delete schedule: {e}")


def cmd_schedule_setup_defaults(args):
    """Handle setup default schedules command."""
    try:
        logger.info(f"🕐 Setting up default schedules for '{args.pipeline_name}'...")
        results = azure_pipeline.setup_default_schedules(args.pipeline_name)

        successful = [k for k, v in results.items() if v is not None]
        failed = [k for k, v in results.items() if v is None]

        if successful:
            logger.info(f"✅ Created {len(successful)} default schedules:")
            for schedule_type in successful:
                logger.info(f"   - {schedule_type}: {results[schedule_type]}")

        if failed:
            logger.warning(
                f"❌ Failed to create {len(failed)} schedules: \
                {', '.join(failed)}"
            )

        logger.info(
            "💡 All schedules are created in disabled state. Use \
            'schedule enable' to activate them."
        )

    except Exception as e:
        logger.error(f"❌ Failed to setup default schedules: {e}")


def get_azure_config():
    """Get Azure configuration from environment variables."""
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    workspace_name = os.getenv("AZURE_WORKSPACE_NAME")

    if not all([subscription_id, resource_group, workspace_name]):
        raise ValueError(
            "Missing required Azure environment variables: "
            "AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_WORKSPACE_NAME"
        )

    return subscription_id, resource_group, workspace_name


def cmd_endpoint_deploy(args):
    """Deploy model to Azure ML Kubernetes endpoint."""
    if AzureMLKubernetesDeployer is None:
        logger.error(
            "❌ Azure ML deployment functionality not available. "
            "Please check azure_endpoint.py imports."
        )
        sys.exit(1)

    try:
        logger.info(f"🚀 Starting Azure ML Kubernetes deployment: {args.endpoint_name}")

        # Initialize deployer for Kubernetes-only deployment
        deployer = AzureMLKubernetesDeployer(env_file=args.env_file)

        # Deploy complete pipeline
        result = deployer.deploy_complete_pipeline(force_update=args.force_update)

        if args.output_json:
            # Save deployment details to JSON file
            with open(args.output_json, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"📄 Deployment details saved to: {args.output_json}")

        logger.info("🎉 Azure ML Kubernetes deployment completed successfully!")
        logger.info(f"📊 Endpoint URI: {result['endpoint']['scoring_uri']}")
        logger.info(
            f"🔑 Primary Key: {result['endpoint']['authentication']['primary_key']}"
        )

    except Exception as e:
        logger.error(f"❌ Kubernetes deployment failed: {e}")
        sys.exit(1)


def cmd_endpoint_test(args):
    """Test the deployed Azure ML endpoint with sample data."""
    try:
        logger.info(f"🧪 Testing Azure ML endpoint: {args.endpoint_name}")

        # Initialize deployer
        deployer = AzureMLKubernetesDeployer(env_file=args.env_file)

        # Test the endpoint
        result = deployer.test_endpoint()

        logger.info("✅ Endpoint test successful")
        logger.info("📊 Test Results:")
        logger.info(f"   Predictions: {result.get('predictions', {})}")
        logger.info(f"   Status: {result.get('status', 'unknown')}")

        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"📝 Test results saved to: {args.output_json}")

    except Exception as e:
        logger.error(f"❌ Endpoint test failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


def cmd_endpoint_details(args):
    """Get detailed information about the Azure ML endpoint."""
    try:
        logger.info(f"📊 Retrieving endpoint details: {args.endpoint_name}")

        # Initialize deployer
        deployer = AzureMLKubernetesDeployer(env_file=args.env_file)

        # Get endpoint details
        details = deployer.get_endpoint_details()

        logger.info("✅ Endpoint details retrieved successfully")
        logger.info("📊 Endpoint Information:")
        logger.info(f"   Name: {details['endpoint_name']}")
        logger.info(f"   State: {details['state']}")
        logger.info(f"   Scoring URI: {details['scoring_uri']}")
        logger.info(f"   Auth Mode: {details['authentication']['auth_mode']}")
        logger.info(f"   Traffic: {details['traffic_allocation']}")

        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump(details, f, indent=2)
            logger.info(f"📝 Endpoint details saved to: {args.output_json}")

    except Exception as e:
        logger.error(f"❌ Failed to get endpoint details: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


def cmd_endpoint_cleanup(args):
    """Delete the Azure ML endpoint and all associated deployments."""
    try:
        if not args.confirm:
            response = input(
                "⚠️ Are you sure you want to delete endpoint ",
                f"'{args.endpoint_name}'? (y/N): ",
            )
            if response.lower() != "y":
                logger.info("❌ Cleanup cancelled by user")
                return

        logger.info(f"🗑️ Cleaning up Azure ML endpoint: {args.endpoint_name}")

        # Initialize deployer
        deployer = AzureMLKubernetesDeployer(env_file=args.env_file)

        # Cleanup endpoint
        deployer.cleanup_endpoint()

        logger.info("✅ Endpoint cleanup completed successfully")

    except Exception as e:
        logger.error(f"❌ Endpoint cleanup failed: {e}")
        if args.verbose:
            traceback.print_exc()
            sys.exit(1)


def cmd_upload_model(args):
    """Upload model artifacts to Azure ML with enhanced packaging."""
    try:
        logger.info("📦 Starting enhanced model upload to Azure ML")

        # Import azure_sync for model upload functionality
        try:
            from .azure_sync import upload_model_with_enhanced_packaging
        except ImportError:
            from azure_sync import upload_model_with_enhanced_packaging

        # Upload model with enhanced packaging
        result = upload_model_with_enhanced_packaging(
            model_name=args.model_name,
            model_version=args.model_version,
            description=args.description,
            tags=args.tags,
        )

        logger.info("✅ Model upload completed successfully")
        logger.info("📊 Upload Results:")
        logger.info(f"   Model Name: {result.get('model_name', 'unknown')}")
        logger.info(f"   Model Version: {result.get('model_version', 'unknown')}")
        logger.info(f"   Upload Status: {result.get('status', 'unknown')}")

        if args.output_json:
            with open(args.output_json, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"📝 Upload details saved to: {args.output_json}")

    except Exception as e:
        logger.error(f"❌ Model upload failed: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


def add_endpoint_deploy_args(parser):
    """Add arguments for Azure ML endpoint deployment command."""
    parser.add_argument(
        "--endpoint-name",
        type=str,
        default="deberta-emotion-clf-endpoint",
        help="Name of the Azure ML endpoint (default: deberta-emotion-clf-endpoint)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to environment file containing Azure credentials (default: .env)",
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Force update existing resources (model, environment, endpoint)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output file to save deployment details in JSON format",
    )


def add_endpoint_test_args(parser):
    """Add arguments for endpoint testing command."""
    parser.add_argument(
        "--endpoint-name",
        type=str,
        default="deberta-emotion-clf-endpoint",
        help="Name of the Azure ML Kubernetes endpoint to test",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to environment file containing Azure credentials",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output file to save test results in JSON format",
    )


def add_endpoint_details_args(parser):
    """Add arguments for getting endpoint details command."""
    parser.add_argument(
        "--endpoint-name",
        type=str,
        default="deberta-emotion-clf-endpoint",
        help="Name of the Azure ML Kubernetes endpoint",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to environment file containing Azure credentials",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output file to save endpoint details in JSON format",
    )


def add_endpoint_cleanup_args(parser):
    """Add arguments for endpoint cleanup command."""
    parser.add_argument(
        "--endpoint-name",
        type=str,
        default="deberta-emotion-clf-endpoint",
        help="Name of the Azure ML Kubernetes endpoint to delete",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to environment file containing Azure credentials",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion without prompting",
    )


def add_upload_model_args(parser):
    """Add arguments for model upload command."""
    parser.add_argument(
        "--model-name",
        type=str,
        default="deberta-endpoint-model",
        help="Registered model name in Azure ML (default: deberta-endpoint-model)",
    )
    parser.add_argument(
        "--model-version",
        type=str,
        help="Version for the model (if not specified, Azure ML will auto-increment)",
    )
    parser.add_argument(
        "--description",
        type=str,
        default="DeBERTa-based emotion classification model with enhanced packaging",
        help="Description for the registered model",
    )
    parser.add_argument(
        "--tags",
        type=str,
        nargs="*",
        help="Tags for the model in key=value format",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output file to save upload details in JSON format",
    )


def main():
    """Main function to parse arguments and execute commands."""
    # Main parser
    parser = argparse.ArgumentParser(
        description="🎭 Emotion Classification Pipeline - \
            Train, predict, and deploy emotion recognition models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete Azure ML pipeline (preprocess + train)
  poetry run python -m emotion_clf_pipeline.cli pipeline --azure --verbose

  # Local prediction
  poetry run python -m emotion_clf_pipeline.cli
  predict "https://youtube.com/watch?v=VIDEO_ID"

  # Azure endpoint prediction (auto-loads config from .env)
  poetry run python -m emotion_clf_pipeline.cli
  predict "https://youtube.com/watch?v=VIDEO_ID" --use-azure

  # Azure prediction with custom endpoint (overrides .env)
  poetry run python -m emotion_clf_pipeline.cli
  predict "https://youtube.com/watch?v=VIDEO_ID" \\
    --use-azure \\
    --azure-endpoint "http://custom-endpoint-url" \\
    --azure-api-key "custom-api-key"

  # Azure with STT and output file
  poetry run python -m emotion_clf_pipeline.cli
  predict "https://youtube.com/watch?v=VIDEO_ID" \\
    --use-azure --use-stt --output results/predictions.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Data command
    parser_data = subparsers.add_parser("data", help="📊 Data preprocessing commands")
    # data_subparsers = parser_data.add_subparsers(dest="data_command")
    parser_data.add_subparsers(dest="data_command")

    # Preprocess command (restored)
    parser_preprocess = subparsers.add_parser(
        "preprocess", help="🔄 Preprocess raw data for training"
    )
    add_preprocess_args(parser_preprocess)
    parser_preprocess.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser_preprocess.add_argument(
        "--mode", choices=["local", "azure"], default="local", help="Execution mode"
    )
    parser_preprocess.add_argument(
        "--azure", action="store_true", help="Use Azure ML for preprocessing"
    )

    # Train command
    parser_train = subparsers.add_parser(
        "train", help="🚀 Train the emotion classification model"
    )
    add_train_args(parser_train)
    parser_train.add_argument(
        "--config", type=str, default="config.json", help="Configuration file path"
    )
    parser_train.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser_train.add_argument(
        "--mode", choices=["local", "azure"], default="local", help="Execution mode"
    )
    parser_train.add_argument(
        "--azure", action="store_true", help="Use Azure ML for training"
    )

    # Pipeline command (complete preprocess + train pipeline)
    parser_pipeline = subparsers.add_parser(
        "pipeline", help="🚀 Run complete pipeline (preprocess + train)"
    )
    add_pipeline_args(parser_pipeline)
    parser_pipeline.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser_pipeline.add_argument(
        "--azure", action="store_true", help="Use Azure ML for pipeline"
    )

    # Predict command with Azure support
    parser_predict = subparsers.add_parser(
        "predict", help="🎭 Predict emotions from video/audio"
    )
    parser_predict.add_argument("input", help="Video URL or file path")
    parser_predict.add_argument("--output", "-o", help="Output file path for results")
    parser_predict.add_argument(
        "--use-stt", action="store_true", help="Use speech-to-text instead of subtitles"
    )
    parser_predict.add_argument(
        "--chunk-size", type=int, default=200, help="Text chunk size for processing"
    )

    # Local model options
    parser_predict.add_argument(
        "--model-path",
        default="models/weights/baseline_weights.pt",
        help="Path to model weights",
    )
    parser_predict.add_argument(
        "--config-path",
        default="models/weights/model_config.json",
        help="Path to model config",
    )

    # Azure endpoint options (auto-loads from .env if not provided)
    parser_predict.add_argument(
        "--use-azure",
        action="store_true",
        help="Use Azure ML endpoint instead of local model",
    )
    parser_predict.add_argument(
        "--azure-endpoint",
        help="Azure ML endpoint URL (overrides AZURE_ENDPOINT_URL from .env)",
    )
    parser_predict.add_argument(
        "--azure-api-key", help="Azure ML API key (overrides AZURE_API_KEY from .env)"
    )
    parser_predict.add_argument(
        "--use-ngrok",
        action="store_true",
        help="Convert endpoint URL to NGROK format (overrides .env)",
    )
    parser_predict.add_argument(
        "--server-ip",
        choices=["226", "227"],
        help="Server IP for NGROK tunnel (overrides AZURE_SERVER_IP from .env)",
    )

    # Endpoint management commands
    parser_endpoint = subparsers.add_parser(
        "endpoint", help="🚀 Azure ML endpoint management"
    )
    endpoint_subparsers = parser_endpoint.add_subparsers(dest="endpoint_command")

    # Deploy endpoint command
    parser_deploy_endpoint = endpoint_subparsers.add_parser(
        "deploy",
        help="Deploy complete ML pipeline to Azure ML Kubernetes endpoint",
    )
    add_endpoint_deploy_args(parser_deploy_endpoint)

    # Test endpoint command
    parser_test_endpoint = endpoint_subparsers.add_parser(
        "test",
        help="Test the deployed Azure ML endpoint with sample data",
    )
    add_endpoint_test_args(parser_test_endpoint)

    # Details endpoint command
    parser_details_endpoint = endpoint_subparsers.add_parser(
        "details",
        help="Get detailed information about the Azure ML endpoint",
    )
    add_endpoint_details_args(parser_details_endpoint)

    # Cleanup endpoint command
    parser_cleanup_endpoint = endpoint_subparsers.add_parser(
        "cleanup",
        help="Delete the Azure ML endpoint and all associated deployments",
    )
    add_endpoint_cleanup_args(parser_cleanup_endpoint)

    # Parse arguments and execute
    args = parser.parse_args()

    if args.command == "data":
        cmd_data(args)
    elif args.command == "preprocess":
        cmd_preprocess(args)
    elif args.command == "train":
        cmd_train(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    elif args.command == "predict":
        cmd_predict(args)
    elif args.command == "endpoint":
        cmd_endpoint(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
