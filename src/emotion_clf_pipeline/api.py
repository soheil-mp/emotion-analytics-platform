"""
Emotion Classification API.

A RESTful API service that analyzes YouTube video content for emotional sentiment.
The service transcribes video audio, processes the text through an emotion
classification pipeline, and returns structured emotion predictions with timestamps.

Key Features:
    - YouTube video transcription using AssemblyAI
    - Multi-dimensional emotion analysis (emotion, sub-emotion, intensity)
    - Time-stamped transcript segmentation
    - CORS-enabled for web frontend integration
    - Feedback collection for training data improvement
    - Comprehensive monitoring with Prometheus metrics
"""

import csv
import io
import json
import logging
import os
import pickle
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Data
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import monitoring components
try:
    from .monitoring import RequestTracker, metrics_collector
except ImportError:
    from monitoring import RequestTracker, metrics_collector

# Import
try:
    from .azure_pipeline import get_ml_client
    from .azure_sync import sync_best_baseline
    from .predict import (  # predict_emotions_local,
        get_video_title,
        predict_emotions_azure,
        process_youtube_url_and_predict,
    )
except ImportError as e:
    print(f"Import error: {e}. Attempting to import from src directory.")
    try:
        from azure_pipeline import get_ml_client
        from azure_sync import sync_best_baseline
        from predict import (  # predict_emotions_local,
            get_video_title,
            predict_emotions_azure,
            process_youtube_url_and_predict,
        )
    except ImportError:
        # Add src directory to path if not already there
        src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from emotion_clf_pipeline.azure_pipeline import get_ml_client
        from emotion_clf_pipeline.azure_sync import sync_best_baseline
        from emotion_clf_pipeline.predict import (  # predict_emotions_local,
            get_video_title,
            predict_emotions_azure,
            process_youtube_url_and_predict,
        )

# Set up logger
logger = logging.getLogger(__name__)

# Application constants
API_TITLE = "Emotion Classification API"
API_VERSION = "0.1.0"
DEFAULT_VIDEO_TITLE = "Unknown Title"
DEFAULT_TRANSCRIPTION_METHOD = "assemblyAI"

# Default values for missing prediction data
DEFAULT_SENTENCE = "N/A"
DEFAULT_TIME = "00:00:00"
DEFAULT_EMOTION = "unknown"
DEFAULT_INTENSITY = "unknown"

# Load environment variables for Azure configuration
load_dotenv()

# Azure configuration
AZURE_ENDPOINT_URL = os.getenv("AZURE_ENDPOINT_URL")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
USE_NGROK = os.getenv("USE_NGROK", "true").lower() == "true"
SERVER_IP = os.getenv("SERVER_IP")

logger.info(f"🌐 Azure config loaded - Endpoint available: {bool(AZURE_ENDPOINT_URL)}")


# FastAPI application configuration
app = FastAPI(
    title=API_TITLE,
    description="""Analyzes YouTube videos for emotional content by transcribing
    audio and applying emotion classification. Returns detailed emotion analysis
    with timestamps for each transcript segment.

    🎯 **Dual Prediction Modes:**
    - **Local (On-Premise)**: Fast local model inference
    - **Azure (Cloud)**: High-accuracy cloud prediction with automatic NGROK tunneling

    🌐 **No VPN Required**: Azure mode automatically converts private endpoints to
    public NGROK URLs
    """,
    version=API_VERSION,
)

# CORS middleware configuration for cross-origin requests
origins = [
    "http://localhost:3000",  # Development frontend
    "http://localhost:3121",  # Alternative development port
    "http://194.171.191.226:3121",  # Production frontend
    "*",  # DEVELOPMENT ONLY - allows all origins for testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEVELOPMENT: allows all origins
    allow_credentials=False,  # Required when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    On application startup, sync the latest baseline model from Azure ML.
    This ensures the API is always using the production-ready model.
    """
    print("🚀 --- Triggering model sync on startup --- 🚀")
    synced = sync_best_baseline(force_update=False, min_f1_improvement=0.0)
    if synced:
        print("✅ --- Model sync successful --- ✅")
    else:
        print("⚠️ --- Model sync failed or no new model found --- ⚠️")

    # Create baseline stats for drift detection if they don't exist
    print("📊 --- Setting up baseline stats for drift detection --- 📊")
    create_baseline_stats_from_training_data()

    # Load training metrics into monitoring system
    print("📊 --- Loading training metrics for monitoring --- 📊")
    load_training_metrics_to_monitoring()


# --- Pydantic Models ---


class PredictionRequest(BaseModel):
    """
    Request payload for emotion prediction endpoint.
    """

    url: str
    method: str = "local"  # "local" for on-premise, "azure" for cloud prediction


class TranscriptItem(BaseModel):
    """
    Represents a single analyzed segment from video transcript.
    """

    sentence: str
    start_time: str
    end_time: str
    emotion: str
    sub_emotion: str
    intensity: str


class PredictionResponse(BaseModel):
    """
    Complete emotion analysis response for a YouTube video.
    """

    videoId: str
    title: str
    transcript: List[TranscriptItem]


class FeedbackItem(BaseModel):
    """
    Represents a single corrected emotion prediction for training data.
    """

    start_time: str
    end_time: str
    text: str
    emotion: str
    sub_emotion: str
    intensity: str


class FeedbackRequest(BaseModel):
    """
    Request payload for submitting emotion classification feedback.
    """

    videoTitle: str
    feedbackData: List[FeedbackItem]


class FeedbackResponse(BaseModel):
    """
    Response for feedback submission.
    """

    success: bool
    filename: str
    message: str
    record_count: int


# --- Helper Functions ---


def convert_azure_result_to_api_format(
    azure_result: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Convert Azure prediction result format to the expected API format.

    Args:
        azure_result: Result from predict_emotions_azure function

    Returns:
        List of predictions in the expected API format
    """
    api_predictions = []

    # Extract transcript data for timestamps
    transcript_data = azure_result.get("transcript_data", {})
    sentences = transcript_data.get("sentences", [])

    # Extract predictions
    predictions = azure_result.get("predictions", [])

    for i, prediction in enumerate(predictions):
        if prediction.get("status") != "success":
            logger.warning(f"Skipping failed prediction at index {i}")
            continue

        # Get the actual emotion predictions
        pred_data = prediction.get("predictions", {})

        # Create API format entry
        api_entry = {
            "text": f"Chunk {i+1}",  # Default text
            "start_time": "00:00:00",  # Default start time
            "end_time": "00:00:00",  # Default end time
            "emotion": pred_data.get("emotion", DEFAULT_EMOTION),
            "sub_emotion": pred_data.get("sub_emotion", DEFAULT_EMOTION),
            "intensity": pred_data.get("intensity", DEFAULT_INTENSITY),
        }

        # Try to match with transcript sentences if available
        if i < len(sentences):
            sentence_data = sentences[i]
            api_entry.update(
                {
                    "text": sentence_data.get("Sentence", api_entry["text"]),
                    "start_time": sentence_data.get(
                        "Start Time", api_entry["start_time"]
                    ),
                    "end_time": sentence_data.get("End Time", api_entry["end_time"]),
                }
            )

        api_predictions.append(api_entry)

    logger.info(f"✅ Converted {len(api_predictions)} Azure predictions to API format")
    return api_predictions


# --- API Endpoints ---


@app.post("/refresh-model")
def handle_refresh() -> Dict[str, Any]:
    """
    Triggers a manual refresh of the baseline model from Azure ML.

    This endpoint allows for a zero-downtime model update by pulling the
    latest model tagged as 'emotion-clf-baseline' from the registry
    and loading it into the running API instance.

    TODO: Secure this endpoint.
    """
    print("🔄 --- Triggering manual model refresh --- 🔄")
    synced = sync_best_baseline(force_update=True, min_f1_improvement=0.0)
    if synced:
        print("✅ --- Model refresh successful --- ✅")
        return {"success": True, "message": "Model refreshed successfully."}

    print("⚠️ --- Model refresh failed or no new model found --- ⚠️")
    return {
        "success": False,
        "message": "Model refresh failed or no new model was found.",
    }


@app.post("/predict", response_model=PredictionResponse)
def handle_prediction(request: PredictionRequest) -> PredictionResponse:
    """
    Analyze YouTube video content for emotional sentiment.
    Supports both local (on-premise) and Azure (cloud) prediction methods.
    """

    with RequestTracker():
        # Generate unique identifier from URL for tracking and caching
        video_id = str(hash(request.url))
        overall_start_time = time.time()

        # Validate prediction method
        if request.method not in ["local", "azure"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid method. Use 'local' for on-premise or \
                    'azure' for cloud prediction.",
            )

        # Check Azure configuration if Azure method is requested
        if request.method == "azure" and (not AZURE_ENDPOINT_URL or not AZURE_API_KEY):
            raise HTTPException(
                status_code=400,
                detail="Azure prediction requested but Azure configuration is \
                    missing. Please set AZURE_ENDPOINT_URL and AZURE_API_KEY \
                    environment variables.",
            )

        logger.info(f"🎯 Processing request with method: {request.method}")

        # Fetch video metadata with graceful error handling
        title_start_time = time.time()
        try:
            video_title = get_video_title(request.url)
            title_latency = time.time() - title_start_time
            logger.info(f"Video title fetch took: {title_latency:.2f}s")
        except Exception as e:
            logger.warning(f"Could not fetch video title: {e}")
            video_title = DEFAULT_VIDEO_TITLE
            metrics_collector.record_error("video_title_fetch", "predict")

        # Process transcription and prediction with detailed timing
        transcription_start_time = time.time()
        try:
            if request.method == "local":
                # Use local on-premise prediction
                logger.info("🖥️ Using local (on-premise) prediction")
                list_of_predictions: List[Dict[str, Any]] = (
                    process_youtube_url_and_predict(
                        youtube_url=request.url,
                        transcription_method=DEFAULT_TRANSCRIPTION_METHOD,
                    )
                )
            else:  # request.method == "azure"
                # Use Azure cloud prediction with automatic NGROK conversion
                logger.info("🌐 Using Azure (cloud) prediction with NGROK")
                result = predict_emotions_azure(
                    video_url=request.url,
                    endpoint_url=AZURE_ENDPOINT_URL,
                    api_key=AZURE_API_KEY,
                    use_stt=False,  # Use transcripts when available
                    chunk_size=200,
                    use_ngrok=USE_NGROK,
                    server_ip=SERVER_IP,
                )

                # Convert Azure result format to expected format
                list_of_predictions = convert_azure_result_to_api_format(result)

            # Record transcription metrics with actual latency
            transcription_latency = time.time() - transcription_start_time
            metrics_collector.transcription_latency.observe(transcription_latency)
            metrics_collector.record_transcription(
                {"text": "transcription_completed"}, latency=transcription_latency
            )
            logger.info(
                f"{request.method.title()} prediction took: \
                    {transcription_latency:.2f}s"
            )

        except Exception as e:
            metrics_collector.record_error("prediction_processing", "predict")
            logger.error(f"Error processing video with {request.method} method: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing video with {request.method} method: {str(e)}",
            )

        # Handle empty results gracefully - return structured empty response
        if not list_of_predictions:
            return PredictionResponse(
                videoId=video_id, title=video_title, transcript=[]
            )

        # Transform raw prediction data into structured transcript items
        prediction_processing_start = time.time()
        transcript_items = []
        for pred in list_of_predictions:
            # Record individual prediction metrics
            sub_emotion = (
                pred.get("sub_emotion", pred.get("sub-emotion", "neutral")) or "neutral"
            )
            intensity_raw = pred.get("intensity", DEFAULT_INTENSITY) or "mild"
            intensity = intensity_raw.lower() if pred.get("intensity") else "mild"

            prediction_data = {
                "emotion": pred.get("emotion", DEFAULT_EMOTION) or DEFAULT_EMOTION,
                "sub_emotion": sub_emotion,
                "intensity": intensity,
            }

            confidence = pred.get("confidence", 0.0)

            # Record model confidence distribution
            metrics_collector.model_confidence.observe(confidence)

            # Record prediction metrics
            pred_latency = time.time() - prediction_processing_start
            metrics_collector.record_prediction(
                prediction_data, confidence=confidence, latency=pred_latency
            )

            transcript_items.append(
                TranscriptItem(
                    sentence=pred.get("text", pred.get("sentence", DEFAULT_SENTENCE)),
                    start_time=format_time_seconds(pred.get("start_time", 0)),
                    end_time=format_time_seconds(pred.get("end_time", 0)),
                    emotion=prediction_data["emotion"],
                    sub_emotion=prediction_data["sub_emotion"],
                    intensity=prediction_data["intensity"],
                )
            )

        # Record overall prediction timing
        overall_latency = time.time() - overall_start_time
        metrics_collector.prediction_latency.observe(overall_latency)
        logger.info(
            f"✅ Total {request.method} prediction processing \
                time: {overall_latency:.2f}s"
        )

        return PredictionResponse(
            videoId=video_id,
            title=video_title,
            transcript=transcript_items,
        )


def get_next_training_filename() -> str:
    """
    Generate the next available training data filename by checking existing files
    in the local data/raw/train directory.
    """
    try:
        # Check local data/raw/train directory for existing files
        train_dir = "data/raw/train"
        if os.path.exists(train_dir):
            existing_files = [
                f
                for f in os.listdir(train_dir)
                if f.startswith("train_data-") and f.endswith(".csv")
            ]

            train_numbers = []
            for filename in existing_files:
                try:
                    # Extract number from filename like "train_data-0001.csv"
                    number_part = filename.replace("train_data-", "").replace(
                        ".csv", ""
                    )
                    train_numbers.append(int(number_part))
                except (ValueError, IndexError):
                    continue

            if train_numbers:
                next_number = max(train_numbers) + 1
            else:
                next_number = 1
        else:
            next_number = 1

        return f"train_data-{next_number:04d}.csv"

    except Exception:
        # Fallback to timestamp-based naming if directory access fails
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"train_data-{timestamp}.csv"


def create_feedback_csv(feedback_data: List[FeedbackItem]) -> str:
    """
    Create CSV content from feedback data.
    """
    output = io.StringIO()

    # Define CSV headers matching the training data format
    fieldnames = [
        "start_time",
        "end_time",
        "text",
        "emotion",
        "sub-emotion",
        "intensity",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    # Write header
    writer.writeheader()

    # Write feedback data
    for item in feedback_data:
        writer.writerow(
            {
                "start_time": item.start_time,
                "end_time": item.end_time,
                "text": item.text,
                "emotion": item.emotion,
                "sub-emotion": item.sub_emotion,  # Note: CSV uses hyphenated version
                "intensity": item.intensity,
            }
        )

    csv_content = output.getvalue()
    output.close()
    return csv_content


def format_time_seconds(time_input) -> str:
    """
    Convert various time formats to HH:MM:SS format.

    Args:
        time_input: Time in seconds (float/int), or already formatted string

    Returns:
        Formatted time string in HH:MM:SS format
    """
    try:
        # If it's already a properly formatted string, return as is
        if isinstance(time_input, str):
            # Check if it's already in HH:MM:SS format
            if ":" in time_input and len(time_input.split(":")) == 3:
                return time_input
            # Try to convert string to float (in case it's "181.5")
            try:
                time_input = float(time_input)
            except ValueError:
                return DEFAULT_TIME

        # Convert numeric seconds to HH:MM:SS
        seconds = float(time_input)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return DEFAULT_TIME


def save_feedback_to_azure(filename: str, csv_content: str) -> bool:
    """
    Save feedback CSV as a new version of the emotion-raw-train Azure ML data asset.
    Creates a new version as URI_FOLDER to match the existing data asset type.
    """
    try:

        ml_client = get_ml_client()

        # Create temporary directory (required for URI_FOLDER type)
        temp_dir = tempfile.mkdtemp(prefix="feedback_upload_")
        try:
            # Step 1: Try to download existing data from latest Azure ML data asset
            try:
                current_asset = ml_client.data.get(
                    name="emotion-raw-train", version="latest"
                )
                print(
                    f"Found existing asset v{current_asset.version}, "
                    f"downloading data..."
                )

                # Download the current asset to get all existing files
                download_path = ml_client.data.download(
                    name="emotion-raw-train", version="latest", download_path=temp_dir
                )
                print(f"Downloaded existing data to: {download_path}")

            except Exception as e:
                print(f"Could not download existing data: {e}")
                # Fallback: Copy from local directory if available
                local_train_dir = "data/raw/train"
                if os.path.exists(local_train_dir):
                    print("Falling back to local training data...")
                    for file in os.listdir(local_train_dir):
                        if file.endswith(".csv"):
                            src_path = os.path.join(local_train_dir, file)
                            dst_path = os.path.join(temp_dir, file)
                            shutil.copy2(src_path, dst_path)

            # Step 2: Add the new feedback file to the collection
            temp_file_path = os.path.join(temp_dir, filename)
            with open(temp_file_path, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)

            # Count total files for reporting
            csv_files = [f for f in os.listdir(temp_dir) if f.endswith(".csv")]
            print(f"Prepared {len(csv_files)} files for new data asset version")

            # Get current asset to determine next version
            try:
                # List all versions of the emotion-raw-train asset
                asset_versions = list(ml_client.data.list(name="emotion-raw-train"))
                if asset_versions:
                    # Find the highest version number
                    version_numbers = []
                    for asset in asset_versions:
                        try:
                            version_numbers.append(int(asset.version))
                        except (ValueError, TypeError):
                            continue

                    if version_numbers:
                        new_version = max(version_numbers) + 1
                    else:
                        new_version = 2
                else:
                    new_version = 2
            except Exception as e:
                print(f"Error getting existing versions: {e}")
                new_version = 2

            # Create new version of the emotion-raw-train data asset as URI_FOLDER
            data_asset = Data(
                name="emotion-raw-train",
                version=str(new_version),
                description=(
                    f"Training data with user feedback - Version {new_version} - "
                    f"Contains {len(csv_files)} files including new "
                    f"feedback: {filename}"
                ),
                path=temp_dir,  # Point to folder containing all CSV files
                type=AssetTypes.URI_FOLDER,  # Match existing asset type
            )  # Register new version with Azure ML (with retry logic)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    created_asset = ml_client.data.create_or_update(data_asset)
                    print(
                        f"Successfully created emotion-raw-train "
                        f"version {new_version}"
                    )
                    print(
                        f"Asset details: {created_asset.name} "
                        f"v{created_asset.version}"
                    )
                    break
                except Exception as retry_error:
                    print(
                        f"Attempt {attempt + 1}/{max_retries} failed: "
                        f"{str(retry_error)}"
                    )
                    if attempt == max_retries - 1:
                        print(
                            "Max retries reached. Data uploaded to storage "
                            "but asset registration failed."
                        )
                        print("The files are safely stored in Azure Storage.")
                    else:
                        time.sleep(2**attempt)  # Exponential backoff

            # Also save locally to maintain consistency
            local_train_dir = "data/raw/train"
            os.makedirs(local_train_dir, exist_ok=True)
            local_file_path = os.path.join(local_train_dir, filename)
            with open(local_file_path, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)

            return True

        finally:
            # Clean up temporary directory after a short delay
            time.sleep(2)  # Give Azure time to process the upload
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"Failed to save feedback to Azure: {str(e)}")
        # Fallback: save locally only
        try:
            local_train_dir = "data/raw/train"
            os.makedirs(local_train_dir, exist_ok=True)
            local_file_path = os.path.join(local_train_dir, filename)
            with open(local_file_path, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)
            print(f"Saved feedback locally to {local_file_path}")
            return True
        except Exception as fallback_error:
            print(f"Failed to save feedback locally: {str(fallback_error)}")
            return False


@app.post("/save-feedback", response_model=FeedbackResponse)
def save_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Save user feedback on emotion predictions as training data.
    """
    try:
        # Validate that we have feedback data
        if not request.feedbackData:
            raise HTTPException(status_code=400, detail="No feedback data provided")

        # Generate filename
        filename = get_next_training_filename()

        # Create CSV content
        csv_content = create_feedback_csv(request.feedbackData)

        # Save to Azure (if available, otherwise just return success for demo)
        try:
            azure_success = save_feedback_to_azure(filename, csv_content)
            if not azure_success:
                # Fallback: could save locally or return partial success
                print(f"Azure save failed, but feedback received: {filename}")
        except Exception as e:
            print(f"Azure integration error: {str(e)}")
            # Continue anyway for demo purposes

        return FeedbackResponse(
            success=True,
            filename=filename,
            message=(
                f"Successfully saved {len(request.feedbackData)} " f"feedback records"
            ),
            record_count=len(request.feedbackData),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving feedback: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to save feedback: {str(e)}"
        )


@app.get("/health")
def health_check() -> Dict[str, str]:
    """
    Docker container health check endpoint.

    Returns 200 OK when the API is ready to serve requests.
    Used by Docker Compose healthcheck configuration.
    """
    return {"status": "healthy", "service": "emotion-classification-api"}


@app.get("/")
def read_root() -> Dict[str, str]:
    """
    API health check and information endpoint.
    """
    return {
        "message": (
            "Welcome to the Emotion Classification API. "
            "Use POST /predict to analyze YouTube videos for emotional content, "
            "or POST /save-feedback to submit training data improvements."
        )
    }


# --- Monitoring Endpoints ---


@app.get("/metrics")
def get_metrics():
    """
    Local monitoring metrics endpoint.

    Exposes comprehensive metrics summary for monitoring the API's
    performance and usage.
    Returns JSON format for easy consumption by monitoring tools.
    """
    try:
        # Export metrics using local metrics collector
        return metrics_collector.get_metrics_summary()
    except Exception as e:
        print(f"Error exporting metrics: {str(e)}")
        return {"error": "Failed to export metrics", "details": str(e)}


@app.get("/monitoring/{file_name}")
async def get_monitoring_file(file_name: str):
    """
    Serve monitoring files for the frontend dashboard with enhanced data processing
    """
    try:
        # Map file names to actual paths
        file_mapping = {
            "api_metrics.json": "results/monitoring/api_metrics.json",
            "model_performance.json": "results/monitoring/model_performance.json",
            "drift_detection.json": "results/monitoring/drift_detection.json",
            "system_metrics.json": "results/monitoring/system_metrics.json",
            "error_tracking.json": "results/monitoring/error_tracking.json",
            "prediction_logs.json": "results/monitoring/prediction_logs.json",
            "daily_summary.json": "results/monitoring/daily_summary.json",
        }

        if file_name not in file_mapping:
            raise HTTPException(
                status_code=404, detail=f"Monitoring file {file_name} not found"
            )

        file_path = Path(file_mapping[file_name])

        if not file_path.exists():
            # Return appropriate empty structure based on file type
            return _get_empty_monitoring_structure(file_name)

        with open(file_path, "r") as f:
            data = json.load(f)

        # Process and enhance data based on file type
        enhanced_data = _enhance_monitoring_data(file_name, data)

        return enhanced_data

    except Exception as e:
        logger.error(f"Error serving monitoring file {file_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading monitoring file: {str(e)}"
        )


@app.get("/monitoring/summary/live")
async def get_live_monitoring_summary():
    """
    Get comprehensive live monitoring summary with real-time calculations
    """
    try:
        summary = {
            "timestamp": datetime.now().isoformat(),
            "status": "online",
            "uptime_seconds": 0,
            "system": {},
            "api": {},
            "model": {},
            "predictions": {},
            "errors": {},
            "health_score": 0,
        }

        # Get system metrics
        try:
            system_file = Path("results/monitoring/system_metrics.json")
            if system_file.exists():
                with open(system_file, "r") as f:
                    system_data = json.load(f)
                if system_data and len(system_data) > 0:
                    latest_system = system_data[-1]
                    recent_system = (
                        system_data[-10:] if len(system_data) >= 10 else system_data
                    )

                    summary["system"] = {
                        "cpu_percent": latest_system.get("cpu_percent", 0),
                        "memory_percent": latest_system.get("memory_percent", 0),
                        "disk_percent": latest_system.get("disk_percent", 0),
                        "memory_used_gb": latest_system.get("memory_used_gb", 0),
                        "memory_available_gb": latest_system.get(
                            "memory_available_gb", 0
                        ),
                        "avg_cpu": sum(m.get("cpu_percent", 0) for m in recent_system)
                        / len(recent_system),
                        "avg_memory": sum(
                            m.get("memory_percent", 0) for m in recent_system
                        )
                        / len(recent_system),
                        "trend": _calculate_system_trend(recent_system),
                    }
        except Exception as e:
            logger.warning(f"Error loading system metrics: {e}")

        # Get API metrics
        try:
            api_file = Path("results/monitoring/api_metrics.json")
            if api_file.exists():
                with open(api_file, "r") as f:
                    api_data = json.load(f)
                if api_data and len(api_data) > 0:
                    latest_api = api_data[-1]
                    recent_api = api_data[-20:] if len(api_data) >= 20 else api_data

                    summary["api"] = {
                        "total_predictions": latest_api.get("total_predictions", 0),
                        "total_errors": latest_api.get("total_errors", 0),
                        "active_requests": latest_api.get("active_requests", 0),
                        "prediction_rate": latest_api.get(
                            "prediction_rate_per_minute", 0
                        ),
                        "error_rate": latest_api.get("error_rate_percent", 0),
                        "avg_latency_ms": (latest_api.get("latency_p50", 0) * 1000),
                        "p95_latency_ms": (latest_api.get("latency_p95", 0) * 1000),
                        "uptime_seconds": latest_api.get("uptime_seconds", 0),
                        "throughput_trend": _calculate_throughput_trend(recent_api),
                    }
                    summary["uptime_seconds"] = latest_api.get("uptime_seconds", 0)
        except Exception as e:
            logger.warning(f"Error loading API metrics: {e}")

        # Get model performance
        try:
            model_file = Path("results/monitoring/model_performance.json")
            if model_file.exists():
                with open(model_file, "r") as f:
                    model_data = json.load(f)
                if model_data and len(model_data) > 0:
                    latest_model = model_data[-1]

                    summary["model"] = {
                        "emotion_f1": latest_model.get("emotion", {}).get("f1", 0),
                        "sub_emotion_f1": latest_model.get("sub_emotion", {}).get(
                            "f1", 0
                        ),
                        "intensity_f1": latest_model.get("intensity", {}).get("f1", 0),
                        "overall_performance": _calculate_overall_performance(
                            latest_model
                        ),
                        "last_updated": latest_model.get("timestamp", ""),
                    }
        except Exception as e:
            logger.warning(f"Error loading model performance: {e}")

        # Get prediction analytics
        try:
            predictions_file = Path("results/monitoring/prediction_logs.json")
            if predictions_file.exists():
                with open(predictions_file, "r") as f:
                    prediction_data = json.load(f)
                if prediction_data and len(prediction_data) > 0:
                    recent_predictions = (
                        prediction_data[-100:]
                        if len(prediction_data) >= 100
                        else prediction_data
                    )

                    emotion_counts = {}
                    confidence_scores = []
                    latencies = []

                    for pred in recent_predictions:
                        emotion = pred.get("emotion", "unknown")
                        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

                        if pred.get("confidence"):
                            confidence_scores.append(pred["confidence"])
                        if pred.get("latency"):
                            latencies.append(pred["latency"])

                    summary["predictions"] = {
                        "total_recent": len(recent_predictions),
                        "dominant_emotion": (
                            max(emotion_counts, key=emotion_counts.get)
                            if emotion_counts
                            else "unknown"
                        ),
                        "emotion_distribution": emotion_counts,
                        "avg_confidence": (
                            sum(confidence_scores) / len(confidence_scores)
                            if confidence_scores
                            else 0
                        ),
                        "avg_latency_ms": (
                            (sum(latencies) / len(latencies) * 1000) if latencies else 0
                        ),
                        "unique_emotions": len(emotion_counts),
                    }
        except Exception as e:
            logger.warning(f"Error loading prediction logs: {e}")

        # Get error summary
        try:
            errors_file = Path("results/monitoring/error_tracking.json")
            if errors_file.exists():
                with open(errors_file, "r") as f:
                    error_data = json.load(f)
                if error_data and len(error_data) > 0:
                    recent_errors = (
                        error_data[-50:] if len(error_data) >= 50 else error_data
                    )

                    error_types = {}
                    severity_counts = {"low": 0, "medium": 0, "high": 0}

                    for error in recent_errors:
                        error_type = error.get("error_type", "unknown")
                        error_types[error_type] = error_types.get(error_type, 0) + 1

                        severity = error.get("severity", "low")
                        if severity in severity_counts:
                            severity_counts[severity] += 1

                    summary["errors"] = {
                        "total_recent": len(recent_errors),
                        "error_types": error_types,
                        "severity_distribution": severity_counts,
                        "most_common_error": (
                            max(error_types, key=error_types.get)
                            if error_types
                            else "none"
                        ),
                    }
        except Exception as e:
            logger.warning(f"Error loading error tracking: {e}")

        # Calculate overall health score
        summary["health_score"] = _calculate_health_score(summary)
        summary["status"] = _determine_system_status(summary["health_score"])

        return summary

    except Exception as e:
        logger.error(f"Error generating live monitoring summary: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating monitoring summary: {str(e)}"
        )


@app.get("/monitoring/analytics/trends")
async def get_monitoring_trends():
    """
    Get trend analysis and predictions for monitoring data
    """
    try:
        trends = {
            "timestamp": datetime.now().isoformat(),
            "performance_trend": "stable",
            "system_trend": "stable",
            "error_trend": "stable",
            "predictions": {},
            "recommendations": [],
        }

        # Analyze API performance trends
        try:
            api_file = Path("results/monitoring/api_metrics.json")
            if api_file.exists():
                with open(api_file, "r") as f:
                    api_data = json.load(f)
                if len(api_data) >= 20:
                    trends["performance_trend"] = _analyze_performance_trend(
                        api_data[-20:]
                    )
        except Exception as e:
            logger.warning(f"Error analyzing performance trends: {e}")

        # Analyze system resource trends
        try:
            system_file = Path("results/monitoring/system_metrics.json")
            if system_file.exists():
                with open(system_file, "r") as f:
                    system_data = json.load(f)
                if len(system_data) >= 30:
                    trends["system_trend"] = _analyze_system_trend(system_data[-30:])
        except Exception as e:
            logger.warning(f"Error analyzing system trends: {e}")

        # Analyze error trends
        try:
            errors_file = Path("results/monitoring/error_tracking.json")
            if errors_file.exists():
                with open(errors_file, "r") as f:
                    error_data = json.load(f)
                if len(error_data) >= 10:
                    trends["error_trend"] = _analyze_error_trend(error_data)
        except Exception as e:
            logger.warning(f"Error analyzing error trends: {e}")

        # Generate recommendations
        trends["recommendations"] = _generate_recommendations(trends)

        return trends

    except Exception as e:
        logger.error(f"Error generating trend analysis: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error generating trend analysis: {str(e)}"
        )


def _get_empty_monitoring_structure(file_name: str):
    """Return appropriate empty structure for missing monitoring files"""
    empty_structures = {
        "api_metrics.json": [],
        "model_performance.json": [],
        "drift_detection.json": [],
        "system_metrics.json": [],
        "error_tracking.json": [],
        "prediction_logs.json": [],
        "daily_summary.json": [],
    }
    return empty_structures.get(file_name, [])


def _enhance_monitoring_data(file_name: str, data):
    """Enhance monitoring data with additional processing"""
    if not data:
        return data

    try:
        # Add trend analysis and summary statistics
        if file_name == "api_metrics.json" and len(data) > 1:
            # Add moving averages and trends
            for i, item in enumerate(data):
                if i >= 5:  # Calculate 5-point moving average
                    recent = data[i - 4 : i + 1]
                    item["latency_ma"] = (
                        sum(r.get("latency_p50", 0) for r in recent) / 5
                    )
                    item["throughput_ma"] = (
                        sum(r.get("prediction_rate_per_minute", 0) for r in recent) / 5
                    )

        elif file_name == "system_metrics.json" and len(data) > 1:
            # Add resource utilization trends
            for i, item in enumerate(data):
                if i >= 10:  # Calculate trends over last 10 readings
                    recent = data[i - 9 : i + 1]
                    item["cpu_trend"] = _calculate_trend(
                        [r.get("cpu_percent", 0) for r in recent]
                    )
                    item["memory_trend"] = _calculate_trend(
                        [r.get("memory_percent", 0) for r in recent]
                    )

    except Exception as e:
        logger.warning(f"Error enhancing {file_name}: {e}")

    return data


def _calculate_system_trend(recent_data):
    """Calculate system resource usage trend"""
    if len(recent_data) < 3:
        return "stable"

    cpu_values = [d.get("cpu_percent", 0) for d in recent_data]
    memory_values = [d.get("memory_percent", 0) for d in recent_data]

    cpu_trend = _calculate_trend(cpu_values)
    memory_trend = _calculate_trend(memory_values)

    if cpu_trend == "increasing" or memory_trend == "increasing":
        return "increasing"
    elif cpu_trend == "decreasing" and memory_trend == "decreasing":
        return "decreasing"
    else:
        return "stable"


def _calculate_throughput_trend(recent_data):
    """Calculate API throughput trend"""
    if len(recent_data) < 5:
        return "stable"

    throughput_values = [d.get("prediction_rate_per_minute", 0) for d in recent_data]
    return _calculate_trend(throughput_values)


def _calculate_trend(values):
    """Calculate trend direction from a series of values"""
    if len(values) < 3:
        return "stable"

    # Simple linear trend calculation
    n = len(values)
    x = list(range(n))
    y = values

    # Calculate slope
    slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (
        n * sum(x[i] ** 2 for i in range(n)) - sum(x) ** 2
    )

    if slope > 0.1:
        return "increasing"
    elif slope < -0.1:
        return "decreasing"
    else:
        return "stable"


def _calculate_overall_performance(model_data):
    """Calculate overall model performance score"""
    try:
        emotion_f1 = model_data.get("emotion", {}).get("f1", 0)
        sub_emotion_f1 = model_data.get("sub_emotion", {}).get("f1", 0)
        intensity_f1 = model_data.get("intensity", {}).get("f1", 0)

        # Weighted average (emotion is most important)
        overall = emotion_f1 * 0.5 + sub_emotion_f1 * 0.3 + intensity_f1 * 0.2
        return round(overall * 100, 2)  # Convert to percentage

    except Exception:
        return 0


def _calculate_health_score(summary):
    """Calculate overall system health score (0-100)"""
    score = 100

    try:
        # System health (40% weight)
        system = summary.get("system", {})
        cpu = system.get("cpu_percent", 0)
        memory = system.get("memory_percent", 0)

        if cpu > 80:
            score -= 20
        elif cpu > 60:
            score -= 10

        if memory > 85:
            score -= 20
        elif memory > 70:
            score -= 10

        # API performance (35% weight)
        api = summary.get("api", {})
        error_rate = api.get("error_rate", 0)
        latency = api.get("avg_latency_ms", 0)

        if error_rate > 5:
            score -= 15
        elif error_rate > 2:
            score -= 8

        if latency > 500:
            score -= 15
        elif latency > 300:
            score -= 8

        # Model performance (25% weight)
        model = summary.get("model", {})
        overall_perf = model.get("overall_performance", 0)

        if overall_perf < 60:
            score -= 15
        elif overall_perf < 75:
            score -= 8

    except Exception as e:
        logger.warning(f"Error calculating health score: {e}")
        score = 50  # Default to moderate health

    return max(0, min(100, score))


def _determine_system_status(health_score):
    """Determine system status based on health score"""
    if health_score >= 90:
        return "excellent"
    elif health_score >= 75:
        return "good"
    elif health_score >= 60:
        return "warning"
    else:
        return "critical"


def _analyze_performance_trend(data):
    """Analyze API performance trend"""
    latencies = [d.get("latency_p50", 0) for d in data]
    throughputs = [d.get("prediction_rate_per_minute", 0) for d in data]

    latency_trend = _calculate_trend(latencies)
    throughput_trend = _calculate_trend(throughputs)

    if latency_trend == "increasing":
        return "degrading"
    elif throughput_trend == "increasing":
        return "improving"
    else:
        return "stable"


def _analyze_system_trend(data):
    """Analyze system resource trend"""
    cpu_values = [d.get("cpu_percent", 0) for d in data]
    memory_values = [d.get("memory_percent", 0) for d in data]

    cpu_trend = _calculate_trend(cpu_values)
    memory_trend = _calculate_trend(memory_values)

    if cpu_trend == "increasing" or memory_trend == "increasing":
        return "deteriorating"
    elif cpu_trend == "decreasing" and memory_trend == "decreasing":
        return "improving"
    else:
        return "stable"


def _analyze_error_trend(data):
    """Analyze error occurrence trend"""
    if len(data) < 10:
        return "stable"

    # Group errors by time periods
    recent_errors = len([e for e in data[-24:] if e])  # Last 24 hours
    older_errors = len([e for e in data[-48:-24] if e])  # Previous 24 hours

    if recent_errors > older_errors * 1.2:
        return "increasing"
    elif recent_errors < older_errors * 0.8:
        return "decreasing"
    else:
        return "stable"


def _generate_recommendations(trends):
    """Generate system recommendations based on trends"""
    recommendations = []

    # Performance recommendations
    if trends["performance_trend"] == "degrading":
        recommendations.append(
            {
                "type": "performance",
                "priority": "high",
                "message": "API latency is increasing. Consider scaling \
                    resources or optimizing model inference.",
                "action": "investigate_latency",
            }
        )

    # System recommendations
    if trends["system_trend"] == "deteriorating":
        recommendations.append(
            {
                "type": "system",
                "priority": "medium",
                "message": "System resources showing upward trend. \
                    Monitor CPU and memory usage closely.",
                "action": "monitor_resources",
            }
        )

    # Error recommendations
    if trends["error_trend"] == "increasing":
        recommendations.append(
            {
                "type": "errors",
                "priority": "high",
                "message": "Error rate is increasing. Review recent \
                    deployments and error logs.",
                "action": "review_errors",
            }
        )

    # Default recommendation if everything is stable
    if not recommendations:
        recommendations.append(
            {
                "type": "general",
                "priority": "low",
                "message": "System is operating within normal parameters. \
                    Continue monitoring.",
                "action": "maintain_monitoring",
            }
        )

    return recommendations


def load_training_metrics_to_monitoring():
    """
    Load training metrics from saved results and update monitoring system.

    This ensures model performance metrics are available in Prometheus
    even after API restarts.
    """
    try:
        # Try to load from results directory first
        base_dir = os.path.dirname(__file__)
        metrics_file_paths = [
            "results/evaluation/training_metrics.json",
            "models/evaluation/metrics.json",
            os.path.join(base_dir, "../../results/evaluation/training_metrics.json"),
            os.path.join(base_dir, "../../models/evaluation/metrics.json"),
        ]

        training_metrics = None
        metrics_file_used = None

        for metrics_path in metrics_file_paths:
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, "r") as f:
                        training_metrics = json.load(f)
                    metrics_file_used = metrics_path
                    break
                except Exception as e:
                    print(f"Failed to load metrics from {metrics_path}: {e}")
                    continue

        if not training_metrics:
            print("⚠️ No training metrics file found - model performance metrics empty")
            return

        print(f"📊 Loading training metrics from: {metrics_file_used}")

        # Extract metrics from the training results
        metrics_to_update = {}

        # Check for training metrics format (newer format)
        if "best_validation_f1s" in training_metrics:
            best_f1s = training_metrics["best_validation_f1s"]
            for task, f1_score in best_f1s.items():
                metrics_to_update[task] = {"f1": f1_score}

        # Check for evaluation epochs format
        elif "epochs" in training_metrics and training_metrics["epochs"]:
            # Get the last epoch's validation metrics
            last_epoch = training_metrics["epochs"][-1]
            if "val_tasks_metrics" in last_epoch:
                val_metrics = last_epoch["val_tasks_metrics"]
                for task, task_metrics in val_metrics.items():
                    metrics_to_update[task] = {
                        "accuracy": task_metrics.get("acc", 0.0),
                        "f1": task_metrics.get("f1", 0.0),
                    }  # Update monitoring system with the loaded metrics
        if metrics_to_update:
            metrics_collector.update_model_performance(metrics_to_update)
            task_list = list(metrics_to_update.keys())
            print(f"✅ Updated monitoring with metrics for tasks: {task_list}")

            # Log the loaded values
            for task, metrics in metrics_to_update.items():
                acc = metrics.get("accuracy", "N/A")
                f1 = metrics.get("f1", "N/A")
                print(f"   - {task}: accuracy={acc}, f1={f1}")
        else:
            print("⚠️ No valid metrics found in training results")

    except Exception as e:
        print(f"❌ Error loading training metrics: {e}")
        # Don't raise - monitoring should continue to work for real-time metrics


def create_baseline_stats_from_training_data():
    """
    Create baseline statistics file for drift detection from training data.

    This creates the baseline_stats.pkl file that the monitoring system
    expects for drift detection to work properly.
    """
    try:
        # Check if baseline stats already exist
        baseline_path = "models/baseline_stats.pkl"
        if os.path.exists(baseline_path):
            print("📊 Baseline stats file already exists")
            return

        # Create basic baseline stats from available training data
        baseline_stats = {
            "feature_means": {},
            "feature_stds": {},
            "prediction_distribution": {
                "happiness": 0.35,
                "neutral": 0.25,
                "sadness": 0.15,
                "anger": 0.10,
                "surprise": 0.08,
                "fear": 0.04,
                "disgust": 0.03,
            },
            "performance_baseline": {"accuracy": 0.60, "f1": 0.58},
        }

        # Ensure the models directory exists
        os.makedirs("models", exist_ok=True)

        # Save the baseline stats
        with open(baseline_path, "wb") as f:
            pickle.dump(baseline_stats, f)

        print(f"✅ Created baseline stats file at: {baseline_path}")

    except Exception as e:
        print(f"⚠️ Could not create baseline stats: {e}")
        # Don't raise - this is not critical for API functionality
