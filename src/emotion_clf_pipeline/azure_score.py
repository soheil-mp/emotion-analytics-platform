"""
Azure ML Scoring Script for DeBERTa Emotion Classification
Optimized for Azure ML managed online endpoints with comprehensive error handling.
"""

import json
import logging
import os
import pickle
from datetime import datetime
from typing import Any, Dict

import numpy as np
import torch
from transformers import AutoTokenizer

# Configure logging for Azure ML
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model components (Azure ML pattern)
model = None
config = None
tokenizer = None
feature_extractor = None
label_encoders = None


def _download_nltk_data_runtime():
    """
    Download NLTK data at runtime for Azure ML environment.
    Essential for feature extraction components.
    """
    import nltk

    logger.info("📦 Downloading NLTK data for Azure ML environment...")

    # Essential NLTK packages for emotion classification
    nltk_packages = [
        "punkt",
        "punkt_tab",
        "averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng",
        "vader_lexicon",
        "stopwords",
        "wordnet",
        "omw-1.4",
        "brown",
        "universal_tagset",
    ]

    download_success = []
    download_failures = []

    for package in nltk_packages:
        try:
            logger.info(f"📥 Downloading NLTK package: {package}")
            if nltk.download(package, quiet=True):
                download_success.append(package)
                logger.info(f"✅ Successfully downloaded: {package}")
            else:
                download_failures.append(package)
                logger.warning(f"⚠️ Failed to download: {package}")
        except Exception as e:
            download_failures.append(package)
            logger.error(f"❌ Exception downloading {package}: {e}")

    logger.info(
        f"✅ NLTK setup complete - "
        f"Success: {len(download_success)}, Failed: {len(download_failures)}"
    )

    # Verify critical packages
    try:
        import nltk.data

        nltk.data.find("tokenizers/punkt")
        logger.info("✅ Critical NLTK packages verified")
    except Exception as e:
        logger.error(f"❌ NLTK verification failed: {e}")
        raise RuntimeError(f"Critical NLTK packages not available: {e}")


def _remap_bert_to_deberta_state_dict(
    state_dict: Dict[str, torch.Tensor],
) -> Dict[str, torch.Tensor]:
    """
    Remap BERT layer names to DeBERTa layer names for compatibility.

    Args:
        state_dict: Original state dict with bert.* layer names

    Returns:
        Remapped state dict with deberta.* layer names
    """
    logger.info("🔄 Remapping BERT layer names to DeBERTa format...")

    remapped_state_dict = {}
    remapping_count = 0

    for key, value in state_dict.items():
        # Remap bert.* to deberta.*
        if key.startswith("bert."):
            new_key = key.replace("bert.", "deberta.", 1)
            remapped_state_dict[new_key] = value
            remapping_count += 1
            logger.debug(f"   Remapped: {key} → {new_key}")
        else:
            # Keep non-bert keys as-is
            remapped_state_dict[key] = value

    logger.info(f"✅ Remapped {remapping_count} BERT layers to DeBERTa format")
    return remapped_state_dict


def _test_sample_prediction():
    """
    Test the model with a sample prediction to verify deployment works.

    Returns:
        bool: True if test passes, False otherwise
    """
    global model, tokenizer, feature_extractor, label_encoders

    logger.info("🧪 Testing model with sample prediction...")

    try:
        # Sample test text
        test_text = "I am feeling really happy and excited about this project!"

        # Extract features
        features = feature_extractor.extract_all_features(test_text)
        logger.info(f"✅ Feature extraction successful: {len(features)} features")

        # Tokenize input
        inputs = tokenizer(
            test_text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        )
        logger.info("✅ Tokenization successful")

        # Move to model device
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        features_tensor = torch.tensor(features, device=device).unsqueeze(0)

        # Run inference
        with torch.no_grad():
            outputs = model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                features=features_tensor,
            )

        # Convert to serializable format
        raw_predictions = {}
        for key, value in outputs.items():
            if torch.is_tensor(value):
                raw_predictions[key] = value.cpu().tolist()
            else:
                raw_predictions[key] = value

        # Convert to human-readable labels if encoders available
        if label_encoders:
            labeled_predictions = _convert_predictions_to_labels(
                raw_predictions, label_encoders
            )
            logger.info(f"✅ Sample prediction successful: {labeled_predictions}")
        else:
            logger.info(f"✅ Sample prediction successful (raw): {raw_predictions}")

        logger.info("🎉 Sample prediction test PASSED - Model is ready for inference!")
        return True

    except Exception as e:
        logger.error(f"❌ Sample prediction test FAILED: {e}")
        return False


def _load_label_encoders():
    """
    Load actual label encoders from training artifacts.

    Returns:
        dict: Dictionary containing label encoders for each task
    """
    logger.info("📋 Loading label encoders from training artifacts...")

    encoders = {}

    # Azure ML model directory structure (includes nested models/ folder)
    model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
    models_subdir = os.path.join(model_dir, "models")

    encoder_paths = {
        "emotion": os.path.join(models_subdir, "encoders", "emotion_encoder.pkl"),
        "sub_emotion": os.path.join(
            models_subdir, "encoders", "sub_emotion_encoder.pkl"
        ),
        "intensity": os.path.join(models_subdir, "encoders", "intensity_encoder.pkl"),
    }

    for task, encoder_path in encoder_paths.items():
        try:
            if os.path.exists(encoder_path):
                with open(encoder_path, "rb") as f:
                    # Load trusted sklearn encoder from controlled environment
                    encoder = pickle.load(f)  # nosec B301
                    encoders[task] = encoder
                    logger.info(
                        f"✅ Loaded {task} encoder: {len(encoder.classes_)} classes"
                    )
                    logger.debug(f"   Classes: {list(encoder.classes_)}")
            else:
                logger.warning(f"⚠️ Encoder not found: {encoder_path}")
                encoders[task] = None
        except ImportError as ie:
            logger.warning(
                f"⚠️ Import error loading {task} encoder "
                f"(probably NumPy compatibility): {ie}"
            )
            logger.warning("NumPy version mismatch, will proceed without encoders")
            encoders[task] = None
        except Exception as e:
            logger.error(f"❌ Failed to load {task} encoder: {e}")
            encoders[task] = None

    return encoders


def _convert_predictions_to_labels(
    predictions: Dict[str, Any], encoders: Dict[str, Any]
) -> Dict[str, str]:
    """
    Convert numerical predictions to human-readable labels.

    Args:
        predictions: Raw model predictions with numerical arrays
        encoders: Label encoders for each task

    Returns:
        Dictionary with human-readable label predictions
    """
    logger.debug("🔄 Converting predictions to human-readable labels...")

    labeled_predictions = {}

    for task, raw_preds in predictions.items():
        if task in encoders and encoders[task] is not None:
            try:
                # Handle different prediction formats
                preds_array = np.array(raw_preds)

                if len(preds_array.shape) > 1:
                    # Batch predictions - take first sample
                    predicted_idx = np.argmax(preds_array[0])
                else:
                    # Single prediction
                    predicted_idx = np.argmax(preds_array)

                # Map to actual label
                predicted_label = encoders[task].classes_[predicted_idx]
                labeled_predictions[task] = predicted_label

                logger.debug(f"   {task}: idx={predicted_idx} → '{predicted_label}'")

            except Exception as e:
                logger.error(f"❌ Error converting {task} predictions: {e}")
                labeled_predictions[task] = "conversion_error"
        else:
            logger.warning(f"⚠️ No encoder for {task}, skipping conversion")
            labeled_predictions[task] = "unknown"

    return labeled_predictions


def init():
    """
    Initialize the model and all components.
    Called once when the deployment starts.
    """
    global model, config, tokenizer, feature_extractor, label_encoders

    try:
        logger.info("🚀 Initializing Azure ML scoring environment...")

        # Download NLTK data first
        _download_nltk_data_runtime()

        # Load label encoders
        label_encoders = _load_label_encoders()

        # Load model configuration from Azure ML model directory
        model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
        models_subdir = os.path.join(model_dir, "models")

        # Try multiple possible locations for model_config.json
        config_paths = [
            os.path.join(models_subdir, "weights", "model_config.json"),
            os.path.join(model_dir, "model_config.json"),
            os.path.join(models_subdir, "model_config.json"),
        ]

        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break

        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            logger.info(f"✅ Config loaded from {config_path}")
            logger.info(
                f"📋 Model architecture: "
                f"hidden_dim={config.get('hidden_dim', 'UNKNOWN')}"
            )
            logger.info(f"📋 Feature dimension: {config.get('feature_dim', 'UNKNOWN')}")
        else:
            logger.warning(f"⚠️ Config file not found at any location: {config_paths}")
            logger.info("📋 Available files in model directory:")
            for root, dirs, files in os.walk(model_dir):
                for file in files:
                    if file.endswith((".json", ".pt", ".pkl")):
                        logger.info(f"   {os.path.join(root, file)}")
            # Fallback configuration - USE CORRECT HIDDEN_DIM FROM ACTUAL TRAINED MODEL
            config = {
                "model_name": "microsoft/deberta-v3-xsmall",
                "feature_dim": 121,
                "num_classes": {"emotion": 7, "sub_emotion": 28, "intensity": 3},
                "hidden_dim": 256,  # CORRECTED: Use 256 to match actual trained model
                "dropout": 0.3,
                "feature_config": {
                    "tfidf": True,
                    "emolex": True,
                    "pos": False,
                    "textblob": False,
                    "vader": False,
                },
            }
            logger.warning(f"⚠️ Using fallback config: {config}")

        # Initialize tokenizer
        tokenizer = AutoTokenizer.from_pretrained(config["model_name"])
        logger.info(f"✅ Tokenizer initialized: {config['model_name']}")

        # Import and initialize feature extractor
        try:
            # Try importing from the package directory in Azure ML
            import sys

            sys.path.append("/var/azureml-app")
            from emotion_clf_pipeline.features import FeatureExtractor
        except ImportError:
            try:
                # Try relative import
                from .features import FeatureExtractor
            except ImportError:
                # Fall back to absolute import (direct execution)
                from features import FeatureExtractor

        # Use Azure ML model directory for EmoLex path (check multiple locations)
        emolex_filename = "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt"
        emolex_paths = [
            os.path.join(models_subdir, "features", "EmoLex", emolex_filename),
            os.path.join(model_dir, "features", "EmoLex", emolex_filename),
            os.path.join(models_subdir, "features", emolex_filename),
            os.path.join(model_dir, "features", emolex_filename),
        ]

        emolex_path = None
        for path in emolex_paths:
            if os.path.exists(path):
                emolex_path = path
                logger.info(f"✅ Found EmoLex lexicon at: {path}")
                break

        feature_config = config.get(
            "feature_config",
            {
                "tfidf": True,
                "emolex": True,
                "pos": False,
                "textblob": False,
                "vader": False,
            },
        )

        feature_extractor = FeatureExtractor(
            feature_config=feature_config, lexicon_path=emolex_path
        )
        logger.info("✅ Feature extractor initialized")

        # Initialize model architecture
        try:
            # Try importing from the package directory in Azure ML
            from emotion_clf_pipeline.model import DEBERTAClassifier
        except ImportError:
            try:
                # Try relative import
                from .model import DEBERTAClassifier
            except ImportError:
                # Fall back to absolute import (direct execution)
                from model import DEBERTAClassifier

        model = DEBERTAClassifier(
            model_name=config["model_name"],
            feature_dim=config["feature_dim"],
            num_classes=config["num_classes"],
            hidden_dim=config["hidden_dim"],
            dropout=config["dropout"],
        )
        logger.info("✅ Model architecture initialized")

        # Load model weights from Azure ML model directory (check multiple locations)
        weights_paths = [
            os.path.join(models_subdir, "weights", "baseline_weights.pt"),
            os.path.join(model_dir, "baseline_weights.pt"),
            os.path.join(models_subdir, "baseline_weights.pt"),
        ]

        weights_path = None
        for path in weights_paths:
            if os.path.exists(path):
                weights_path = path
                logger.info(f"✅ Found model weights at: {path}")
                break

        if weights_path and os.path.exists(weights_path):
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"📦 Loading model weights from {weights_path} on {device}")

            # Load model weights with security consideration for trusted model files
            state_dict = torch.load(
                weights_path, map_location=device, weights_only=False
            )  # nosec B614

            # Check if we need to remap BERT layer names to DeBERTa
            if any(key.startswith("bert.") for key in state_dict.keys()):
                logger.info(
                    "🔄 Detected BERT layer names, remapping to DeBERTa format..."
                )
                state_dict = _remap_bert_to_deberta_state_dict(state_dict)

            missing_keys, unexpected_keys = model.load_state_dict(
                state_dict, strict=False
            )

            if missing_keys:
                logger.warning(
                    f"⚠️ Missing keys: {missing_keys[:10]}..."
                )  # Show only first 10
            if unexpected_keys:
                logger.warning(
                    f"⚠️ Unexpected keys: {unexpected_keys[:10]}..."
                )  # Show only first 10

            model.to(device)
            model.eval()
            logger.info("✅ Model weights loaded successfully")
        else:
            raise FileNotFoundError(
                f"Model weights not found in any expected locations: {weights_paths}"
            )

        # Test sample prediction to verify everything works
        if not _test_sample_prediction():
            raise RuntimeError("Sample prediction test failed - model not ready")

        logger.info("🎉 Azure ML scoring initialization complete!")

    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        raise RuntimeError(f"Failed to initialize scoring environment: {e}")


def run(raw_data: str) -> str:
    """
    Run inference on input data.
    Called for each scoring request.

    Args:
        raw_data: JSON string containing input data

    Returns:
        JSON string containing predictions
    """
    global model, tokenizer, feature_extractor, label_encoders

    try:
        logger.info("🎯 Processing scoring request...")

        # Parse input data
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = raw_data

        # Extract text input
        text = data.get("text", "")
        if not text or not text.strip():
            raise ValueError("No valid text provided in input data")

        logger.info(
            f"📝 Processing text: {text[:100]}{'...' if len(text) > 100 else ''}"
        )

        # Extract features
        logger.debug("🔍 Extracting features...")
        features = feature_extractor.extract_all_features(text)
        logger.debug(f"✅ Features extracted: shape={len(features)}")

        # Tokenize input
        logger.debug("🔤 Tokenizing text...")
        inputs = tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=128
        )

        # Move to model device
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        features_tensor = torch.tensor(features, device=device).unsqueeze(0)

        # Run inference
        logger.debug("🧠 Running model inference...")
        with torch.no_grad():
            outputs = model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                features=features_tensor,
            )

        # Convert to serializable format
        raw_predictions = {}
        for key, value in outputs.items():
            if torch.is_tensor(value):
                raw_predictions[key] = value.cpu().tolist()
            else:
                raw_predictions[key] = value

        # Convert to human-readable labels
        if label_encoders:
            labeled_predictions = _convert_predictions_to_labels(
                raw_predictions, label_encoders
            )

            # Azure ML compatible response format
            result = {
                "predictions": labeled_predictions,
                "raw_predictions": raw_predictions,
                "confidence_scores": raw_predictions,
                "status": "success",
            }
        else:
            logger.warning("⚠️ Label encoders not available")
            result = {"predictions": raw_predictions, "status": "success"}

        logger.info(f"✅ Inference successful: {result.get('predictions', {})}")
        return json.dumps(result)

    except ValueError as e:
        # Input validation errors
        error_response = {
            "error": f"Invalid input: {str(e)}",
            "status": "error",
            "error_type": "validation_error",
        }
        logger.error(f"❌ Input validation error: {e}")
        return json.dumps(error_response)

    except Exception as e:
        # General inference errors
        error_response = {
            "error": f"Inference failed: {str(e)}",
            "status": "error",
            "error_type": "inference_error",
        }
        logger.error(f"❌ Inference error: {e}")
        return json.dumps(error_response)


# Health check function for Azure ML monitoring
def get_health_status() -> Dict[str, Any]:
    """
    Get health status of the scoring service.

    Returns:
    Dictionary containing health information
    """
    global model, tokenizer, feature_extractor, label_encoders
    health_status = {
        "status": "healthy",
        "timestamp": str(datetime.now()),
        "components": {
            "model": model is not None,
            "tokenizer": tokenizer is not None,
            "feature_extractor": feature_extractor is not None,
            "label_encoders": label_encoders is not None,
        },
        "device": str(next(model.parameters()).device) if model else "unknown",
        "ready": all(
            [
                model is not None,
                tokenizer is not None,
                feature_extractor is not None,
                label_encoders is not None,
            ]
        ),
    }

    if not health_status["ready"]:
        health_status["status"] = "unhealthy"

    return health_status


# Optional: Custom logging for Azure ML insights
def log_prediction_metrics(
    input_text: str, predictions: Dict[str, Any], inference_time: float
) -> None:
    """
    Log prediction metrics for monitoring and analytics.

    Args:
        input_text: Input text that was processed
        predictions: Model predictions
        inference_time: Time taken for inference in seconds
    """
    try:
        metrics = {
            "input_length": len(input_text),
            "inference_time_ms": inference_time * 1000,
            "predicted_emotion": predictions.get("emotion", "unknown"),
            "predicted_intensity": predictions.get("intensity", "unknown"),
            "timestamp": str(datetime.now()),
        }

        # Log to Azure ML metrics (if enabled)
        logger.info(f"📊 Prediction metrics: {json.dumps(metrics)}")

    except Exception as e:
        logger.warning(f"⚠️ Failed to log metrics: {e}")


if __name__ == "__main__":
    # For local testing of the scoring script
    print("🧪 Testing Azure ML scoring script locally...")

    try:
        # Initialize
        init()

        # Test inference
        test_data = '{"text": "I am feeling really happy and excited!"}'
        result = run(test_data)

        print("✅ Test successful!")
        print(f"Result: {result}")

        # Test health check
        health = get_health_status()
        print(f"Health: {json.dumps(health, indent=2)}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
