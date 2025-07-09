#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A complete end-to-end pipeline for extracting and analyzing emotional content
from YouTube videos. This module orchestrates the entire workflow from audio
extraction to emotion classification, providing a streamlined interface for
sentiment analysis research and applications.

The pipeline supports multiple transcription services with automatic fallback
mechanisms to ensure robustness in production environments.

Usage:
    python predict.py "https://youtube.com/watch?v=..." --transcription_method whisper
"""

# Standard library imports for core functionality
import argparse
import json
import logging
import os
import pickle
import time
import urllib.error
import urllib.request
import warnings
from typing import Any, Dict, List, Optional

import numpy as np

# Third-party imports for data processing and external services
import pandas as pd
from dotenv import load_dotenv
from pytubefix import YouTube

# Import domain-specific modules for pipeline components
try:
    # Try relative imports first (when used as a package)
    from .features import FeatureExtractor
    from .model import DEBERTAClassifier, EmotionPredictor
    from .stt import (
        SpeechToTextTranscriber,
        WhisperTranscriber,
        save_youtube_audio,
        save_youtube_video,
    )
except ImportError:
    # Fallback to absolute imports from the package (when API imports this module)
    from emotion_clf_pipeline.features import FeatureExtractor
    from emotion_clf_pipeline.model import DEBERTAClassifier, EmotionPredictor
    from emotion_clf_pipeline.stt import (
        SpeechToTextTranscriber,
        WhisperTranscriber,
        save_youtube_audio,
        save_youtube_video,
    )

# Initialize logger
logger = logging.getLogger(__name__)


def _remap_bert_to_deberta_state_dict(state_dict: Dict[str, Any]) -> Dict[str, Any]:
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


def extract_transcript(video_url: str) -> Dict[str, Any]:
    """Extract transcript from YouTube video using subtitles (fallback to STT)."""
    logger.info(f"🎬 Extracting transcript from: {video_url}")

    try:
        # Try subtitle extraction first using yt-dlp
        import yt_dlp

        ydl_opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "skip_download": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # Try to get manual subtitles first, then automatic
            subtitles = info.get("subtitles", {}).get("en") or info.get(
                "automatic_captions", {}
            ).get("en")

            if subtitles:
                # Get the first available subtitle format
                subtitle_url = subtitles[0]["url"]

                # Download and parse subtitles
                import urllib.request

                with urllib.request.urlopen(subtitle_url) as response:
                    subtitle_content = response.read().decode("utf-8")

                # Simple text extraction (you might want to use a proper VTT/SRT parser)
                import re

                text = re.sub(r"<[^>]+>", "", subtitle_content)  # Remove HTML tags
                text = re.sub(
                    r"\d+:\d+:\d+\.\d+ --> \d+:\d+:\d+\.\d+", "", text
                )  # Remove timestamps
                text = " ".join(
                    line.strip() for line in text.split("\n") if line.strip()
                )

                logger.info(
                    f"✅ Subtitle extraction successful: {len(text)} characters"
                )

                return {
                    "text": text,
                    "source": "subtitles",
                    "video_url": video_url,
                    "title": info.get("title", "Unknown"),
                }
            else:
                raise ValueError("No subtitles available")

    except Exception as e:
        logger.warning(f"⚠️ Subtitle extraction failed: {e}")
        logger.info("🎤 Falling back to speech-to-text...")
        return extract_audio_transcript(video_url)


def extract_audio_transcript(video_url: str) -> Dict[str, Any]:
    """Extract transcript using speech-to-text from stt.py."""
    logger.info(f"🎤 Starting STT transcription for: {video_url}")

    try:
        # Download audio first using stt.py function
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Download YouTube audio using stt.py function
            audio_file, title = save_youtube_audio(video_url, temp_dir)
            logger.info(f"📥 Audio downloaded: {title}")

            # Use Whisper transcriber from stt.py
            transcriber = WhisperTranscriber(model_size="base")

            # Transcribe the audio file using the existing API
            result = transcriber.transcribe_audio(audio_file)

            # Extract sentences with timestamps using the existing method
            transcript_data = transcriber.extract_sentences(result)

            # Combine all sentences into full text
            full_text = " ".join([item["Sentence"] for item in transcript_data])

            logger.info(f"✅ STT transcription successful: {len(full_text)} characters")

            return {
                "text": full_text,
                "source": "stt_whisper",
                "video_url": video_url,
                "title": title,
                "segments": result.get("segments", []),
                "sentences": transcript_data,  # Include structured sentence data
            }

    except Exception as e:
        logger.error(f"❌ STT extraction failed: {e}")
        raise ValueError(f"Failed to extract transcript using STT: {e}")


def transcribe_youtube_url(video_url: str, use_stt: bool = False) -> Dict[str, Any]:
    """
    Main transcription function that chooses between subtitle and STT methods.

    Args:
        video_url: YouTube video URL
        use_stt: If True, force use of speech-to-text. If False, try subtitles first.

    Returns:
        Dictionary containing transcript data and metadata
    """
    if use_stt:
        logger.info("🎤 Forcing STT transcription (--use-stt flag)")
        return extract_audio_transcript(video_url)
    else:
        logger.info("📝 Attempting subtitle extraction first...")
        return extract_transcript(video_url)


# Silence non-critical warnings to improve user experience
warnings.filterwarnings("ignore")

# Load environment variables from .env file
load_dotenv()

# Configure structured logging for better debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Azure endpoint configuration from environment variables
AZURE_CONFIG = {
    "endpoint_url": os.getenv("AZURE_ENDPOINT_URL"),
    "api_key": os.getenv("AZURE_API_KEY"),
    "use_ngrok": os.getenv("AZURE_USE_NGROK", "false").lower() == "true",
    "server_ip": os.getenv("AZURE_SERVER_IP", "227"),
}

# Establish project directory structure for consistent file operations
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(CURRENT_DIR))  # Project root
DATA_DIR = os.path.join(BASE_DIR, "data")


def get_azure_config(
    endpoint_url: Optional[str] = None,
    api_key: Optional[str] = None,
    use_ngrok: Optional[bool] = None,
    server_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Azure endpoint configuration with fallback priorities.

    Priority order:
    1. Explicit parameters passed to function
    2. Environment variables from .env file
    3. Raise error if required values missing

    Args:
        endpoint_url: Azure ML endpoint URL (override .env)
        api_key: Azure ML API key (override .env)
        use_ngrok: Use NGROK tunnel (override .env)
        server_ip: Server IP for NGROK (override .env)

    Returns:
        Dictionary with Azure configuration

    Raises:
        ValueError: If required configuration is missing
    """
    config = {
        "endpoint_url": endpoint_url or AZURE_CONFIG["endpoint_url"],
        "api_key": api_key or AZURE_CONFIG["api_key"],
        "use_ngrok": use_ngrok if use_ngrok is not None else AZURE_CONFIG["use_ngrok"],
        "server_ip": server_ip or AZURE_CONFIG["server_ip"],
    }

    # Validate required configuration
    if not config["endpoint_url"]:
        raise ValueError(
            "Azure endpoint URL not found. Please set AZURE_ENDPOINT_URL in .env file "
            "or pass --azure-endpoint parameter."
        )

    if not config["api_key"]:
        raise ValueError(
            "Azure API key not found. Please set AZURE_API_KEY in .env file "
            "or pass --azure-api-key parameter."
        )

    logger.info(
        f"🔧 Azure config loaded - NGROK: {config['use_ngrok']}, ",
        f"Server: {config['server_ip']}",
    )
    return config


def time_str_to_seconds(time_str):
    """
    Convert time strings to seconds for numerical operations.

    Handles multiple time formats commonly found in transcription outputs:
    - HH:MM:SS or HH:MM:SS.mmm (hours, minutes, seconds with optional milliseconds)
    - MM:SS or MM:SS.mmm (minutes, seconds with optional milliseconds)
    - Numeric values (already in seconds)

    This conversion is essential for temporal analysis and synchronization
    between audio timestamps and emotion predictions.

    Args:
        time_str: Time in string format or numeric value

    Returns:
        float: Time converted to seconds, or 0.0 if parsing fails
          Note:
        Returns 0.0 for invalid inputs rather than raising exceptions
        to maintain pipeline robustness during batch processing.
    """

    # Return early if time_str is already numeric
    if isinstance(time_str, (int, float)):
        return float(time_str)

    # Error handling
    try:

        # Split time string into components
        parts = str(time_str).split(":")

        # Handle HH:MM:SS or MM:SS formats with optional milliseconds
        if len(parts) == 3:
            h, m, s_parts = parts
            s_and_ms = s_parts.split(".")
            s = float(s_and_ms[0])
            ms = float(s_and_ms[1]) / 1000.0 if len(s_and_ms) > 1 else 0.0
            return float(h) * 3600 + float(m) * 60 + s + ms

        # Handle MM:SS format with optional milliseconds
        elif len(parts) == 2:
            m, s_parts = parts
            s_and_ms = s_parts.split(".")
            s = float(s_and_ms[0])
            ms = float(s_and_ms[1]) / 1000.0 if len(s_and_ms) > 1 else 0.0
            return float(m) * 60 + s + ms

        # Handle numeric values directly
        else:
            return float(time_str)

    # Catch parsing errors and log warnings
    except ValueError:
        logger.warning(f"Could not parse time string: {time_str}. Returning 0.0")
        return 0.0


def get_video_title(youtube_url: str) -> str:
    """
    Extract video title from YouTube URL for meaningful file naming.

    Video titles serve as natural identifiers for organizing processing
    results and enable easy correlation between source content and
    analysis outputs.

    Args:
        youtube_url: Valid YouTube video URL

    Returns:
        str: Video title or "Unknown Title" if extraction fails

    Note:
        Gracefully handles network errors and invalid URLs to prevent
        pipeline interruption during batch processing scenarios.
    """
    # Initialize YouTube object and fetch video title
    try:
        yt = YouTube(youtube_url, use_po_token=False)
        return yt.title

    # Handle exceptions during title extraction
    except Exception as e:
        logger.error(f"Error fetching YouTube video title for {youtube_url}: {e}")
        return "Unknown Title"


def predict_emotion(texts, feature_config=None, reload_model=False):
    """
    Apply emotion classification to text using trained models.

    This function serves as the core intelligence of the pipeline,
    transforming raw text into structured emotional insights. It supports
    both single text analysis and batch processing for efficiency.

    Args:
        texts: Single text string or list of texts for analysis
        feature_config: Optional configuration for feature extraction methods
        reload_model: Force model reinitialization (useful for memory management)

    Returns:
        dict or list: Emotion predictions with confidence scores.
                     Single dict for one text, list of dicts for multiple texts.
                     Returns None if prediction fails.

    Performance:
        Logs processing latency for performance monitoring and optimization.
    """

    # Initialize emotion predictor with optional model reload
    _emotion_predictor = EmotionPredictor()

    # Start timer
    start = time.time()

    # Error handling
    try:

        # Predict emotion for single text or batch
        output = _emotion_predictor.predict(texts, feature_config, reload_model)

        # End timer
        end = time.time()
        logger.info(f"Latency (Emotion Classification): {end - start:.2f} seconds")

        return output

    # Catch exceptions during prediction
    except Exception as e:
        logger.error(f"Error in emotion prediction: {str(e)}")
        return None


def speech_to_text(transcription_method, audio_file, output_file):
    """
    Convert audio to text using configurable transcription services.

    Implements a robust transcription strategy with automatic fallback:
    - Primary: AssemblyAI (cloud-based, high accuracy)
    - Fallback: Whisper (local processing, privacy-preserving)

    This dual-service approach ensures pipeline reliability even when
    external services are unavailable or API limits are reached.

    Args:
        transcription_method: "assemblyAI" or "whisper" for primary service
        audio_file: Path to input audio file
        output_file: Path where transcript will be saved

    Raises:
        ValueError: If transcription_method is not recognized

    Note:
        AssemblyAI failures trigger automatic Whisper fallback.
        All transcription attempts are logged for debugging purposes.
    """

    # Start timer
    start = time.time()

    # Initialize variables
    transcription_successful = False
    method_used = transcription_method.lower()

    # If "AssemblyAI" is specified
    if method_used == "assemblyai":

        # Error handling
        try:

            # Load AssemblyAI API key
            load_dotenv(dotenv_path="/app/.env", override=True)
            api_key = os.environ.get("ASSEMBLYAI_API_KEY")

            # Transcribe using AssemblyAI
            transcriber = SpeechToTextTranscriber(api_key)
            transcriber.process(audio_file, output_file)
            transcription_successful = True
            logger.info("AssemblyAI transcription successful.")

        # Catch exceptions during AssemblyAI transcription
        except Exception as e_assembly:
            logger.error(f"Error: AssemblyAI transcription: {str(e_assembly)}.")

        # Automatic fallback mechanism for reliability
        if not transcription_successful:
            method_used = "whisper"
            logger.info("Falling back to Whisper transcription")

    # If "Whisper" is specified or fallback is triggered
    if method_used == "whisper":

        # Error handling
        try:

            # Transcribe using Whisper
            transcriber = WhisperTranscriber()
            transcriber.process(audio_file, output_file)
            transcription_successful = True
            logger.info("Whisper transcription successful.")

        # Catch exceptions during Whisper transcription
        except Exception as e_whisper:
            logger.error(f"Error during Whisper transcription: {str(e_whisper)}")

    # If transcription method is not recognized
    if method_used not in ["assemblyai", "whisper"]:
        logger.error(f"Unknown transcription method: {transcription_method}")
        raise ValueError(f"Unknown transcription method: {transcription_method}")

    # End timer
    end = time.time()

    # Show latency metrics if transcription was successful
    if transcription_successful:
        logger.info(f"Latency (Speech-to-Text with {method_used}): {end - start:.2f} s")
    else:
        logger.warning(
            f"Speech-to-Text failed for '{transcription_method}' "
            f"(and fallback if applicable) after {end - start:.2f} s."
        )


def process_youtube_url_and_predict(
    youtube_url: str, transcription_method: str
) -> list[dict]:
    """
    Execute the complete emotion analysis pipeline for a YouTube video.
      This is the main orchestration function that coordinates all pipeline stages:
    1. Audio extraction from YouTube (with title metadata)
    2. Speech-to-text transcription (with fallback mechanisms)
    3. Emotion classification (with temporal alignment)
    4. Results persistence (structured Excel output)

    The function maintains data lineage throughout the process, ensuring
    that timestamps from transcription are preserved and aligned with
    emotion predictions for temporal analysis capabilities.

    Args:
        youtube_url: Valid YouTube video URL for processing
        transcription_method: "assemblyAI" or "whisper" for speech recognition

    Returns:
        list[dict]: Structured emotion analysis results where each dictionary
                   contains temporal and emotional metadata:
                   - start_time/end_time: Temporal boundaries of the segment
                   - text: Transcribed speech content
                   - emotion/sub_emotion: Classified emotional states
                   - intensity: Emotional intensity measurement

    Returns empty list if essential processing steps fail.

    Note:
        Creates necessary output directories automatically.
        All intermediate and final results are persisted to disk
        for reproducibility and further analysis.
    """  # Initialize directories
    youtube_audio_dir = os.path.join(BASE_DIR, "results", "audio")
    youtube_video_dir = os.path.join(BASE_DIR, "results", "video")
    transcripts_dir = os.path.join(BASE_DIR, "results", "transcript")
    results_dir = os.path.join(BASE_DIR, "results", "predictions")

    # Make sure output directories exist
    os.makedirs(youtube_audio_dir, exist_ok=True)
    os.makedirs(youtube_video_dir, exist_ok=True)
    os.makedirs(transcripts_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    # STAGE 1A: Audio Extraction with Metadata
    logger.info("*" * 50)
    logger.info("Step 1a - Downloading YouTube audio...")

    actual_audio_path, title = save_youtube_audio(
        url=youtube_url,
        destination=youtube_audio_dir,
    )
    logger.info(f"Audio file saved at: {actual_audio_path}")
    logger.info("YouTube audio downloaded successfully!")

    # STAGE 1B: Video Extraction with Metadata
    logger.info("*" * 50)
    logger.info("Step 1b - Downloading YouTube video...")

    try:
        actual_video_path, _ = save_youtube_video(
            url=youtube_url,
            destination=youtube_video_dir,
        )
        logger.info(f"Video file saved at: {actual_video_path}")
        logger.info("YouTube video downloaded successfully!")
    except Exception as e:
        logger.warning(f"Video download failed: {str(e)}")
        logger.info("Continuing with audio processing only...")

    # STAGE 2: Speech Recognition with Fallback Strategy
    logger.info("*" * 50)
    logger.info("Step 2 - Transcribing audio...")
    transcript_output_file = os.path.join(
        transcripts_dir,
        f"{title}.xlsx",
    )
    speech_to_text(transcription_method, actual_audio_path, transcript_output_file)

    # Load and validate transcript structure
    df = pd.read_excel(transcript_output_file)
    df = df.dropna(subset=["Sentence"])  # Remove empty sentences
    df = df.reset_index(drop=True)  # Clean up row indices

    # Initialize results container
    sentences_data = []

    # Validate that transcript has required columns for processing
    if (
        "Sentence" in df.columns
        and "Start Time" in df.columns
        and "End Time" in df.columns
    ):
        # Extract structured data from transcript
        sentences = df["Sentence"].tolist()
        start_times_str = df["Start Time"].tolist()
        end_times_str = df["End Time"].tolist()

        logger.info(
            f"Transcription completed successfully! "
            f"Found {len(sentences)} sentences."
        )

        # STAGE 3: Emotion Analysis with Temporal Alignment
        logger.info("*" * 50)
        logger.info("Step 3 - Classifying emotions, sub-emotions, and intensity...")

        emotion_predictions = []
        if sentences:
            # Process all sentences in batch for efficiency
            emotion_predictions = predict_emotion(sentences)
        else:
            logger.info("Info: No sentences found for emotion classification.")

        # Combine temporal and emotional data for comprehensive analysis
        for i, sentence_text in enumerate(sentences):
            # Initialize data structure with temporal boundaries
            pred_data = {
                "start_time": start_times_str[i],
                "end_time": end_times_str[i],
                "text": sentence_text,
                "emotion": "unknown",
                "sub_emotion": "unknown",
                "intensity": "unknown",
            }
            # Merge emotion predictions if available
            if (
                emotion_predictions
                and i < len(emotion_predictions)
                and emotion_predictions[i]
            ):
                pred_data["emotion"] = emotion_predictions[i].get("emotion", "unknown")
                pred_data["sub_emotion"] = emotion_predictions[i].get(
                    "sub_emotion", "unknown"
                )
                # Ensure intensity is string for consistent output format
                pred_data["intensity"] = str(
                    emotion_predictions[i].get("intensity", "unknown")
                )
            sentences_data.append(pred_data)
    else:
        logger.warning(
            "One or more required columns (Sentence, Start Time, End Time) "
            "are missing from the transcript Excel file."
        )
        # Return empty list if essential columns are missing
        return []  # STAGE 4: Results Persistence for Reproducibility
    results_df = pd.DataFrame(sentences_data)
    results_file = os.path.join(results_dir, f"{title}.xlsx")
    # Save structured results with temporal and emotional metadata
    results_df.to_excel(results_file, index=False)
    logger.info(f"Emotion predictions saved to {results_file}")
    logger.info("*" * 50)

    return sentences_data


class AzureEndpointPredictor:
    """
    A class to interact with an Azure endpoint for emotion classification.
    It handles API requests, decodes predictions, and post-processes sub-emotions.
    """

    def __init__(self, api_key, endpoint_url, encoders_dir="models/encoders"):
        """
        Initialize with API key, endpoint URL, and encoder directory.
        Automatically converts private network URLs to public NGROK URLs.
        """
        self.api_key = api_key
        self.endpoint_url = self._convert_to_ngrok_url(endpoint_url)
        self.encoders_dir = encoders_dir

        logger.info(f"🌐 Azure endpoint initialized with NGROK: {self.endpoint_url}")
        self.emotion_mapping = {
            "curiosity": "happiness",
            "neutral": "neutral",
            "annoyance": "anger",
            "confusion": "surprise",
            "disappointment": "sadness",
            "excitement": "happiness",
            "surprise": "surprise",
            "realization": "surprise",
            "desire": "happiness",
            "approval": "happiness",
            "disapproval": "disgust",
            "embarrassment": "fear",
            "admiration": "happiness",
            "anger": "anger",
            "optimism": "happiness",
            "sadness": "sadness",
            "joy": "happiness",
            "fear": "fear",
            "remorse": "sadness",
            "gratitude": "happiness",
            "disgust": "disgust",
            "love": "happiness",
            "relief": "happiness",
            "grief": "sadness",
            "amusement": "happiness",
            "caring": "happiness",
            "nervousness": "fear",
            "pride": "happiness",
        }
        self._load_encoders()

    def _convert_to_ngrok_url(self, endpoint_url: str) -> str:
        """
        Automatically convert private network URLs to public NGROK URLs.
        No more VPN needed!

        Args:
            endpoint_url: Original endpoint URL (private network)

        Returns:
            Converted NGROK URL (public access)
        """
        # If already an NGROK URL, return as-is
        if "ngrok" in endpoint_url:
            logger.info("🔗 URL already in NGROK format")
            return endpoint_url

        logger.info(f"🔄 Converting private URL to NGROK: {endpoint_url}")

        # Server 226 conversion
        if "194.171.191.226" in endpoint_url:
            ngrok_url = endpoint_url.replace(
                "http://194.171.191.226:", "https://cradle.buas.ngrok.app/port-"
            )
            logger.info(f"✅ Converted to server 226 NGROK: {ngrok_url}")
            return ngrok_url

        # Server 227 conversion (updated URL as per guide)
        elif "194.171.191.227" in endpoint_url:
            ngrok_url = endpoint_url.replace(
                "http://194.171.191.227:", "https://adsai2.ngrok.dev/port-"
            )
            logger.info(f"✅ Converted to server 227 NGROK: {ngrok_url}")
            return ngrok_url

        # If no conversion needed, return original
        else:
            logger.info("ℹ️ No conversion needed, using original URL")
            return endpoint_url

    def _load_encoders(self):
        """
        Load label encoders for emotion, sub_emotion, and intensity.
        Includes hardcoded fallbacks if files are corrupted/missing.
        """
        # Hardcoded fallback mappings based on training data
        HARDCODED_ENCODERS = {
            "emotion": {
                "classes_": [
                    "anger",
                    "disgust",
                    "fear",
                    "happiness",
                    "neutral",
                    "sadness",
                    "surprise",
                ],
                "label_to_idx": {
                    "anger": 0,
                    "disgust": 1,
                    "fear": 2,
                    "happiness": 3,
                    "neutral": 4,
                    "sadness": 5,
                    "surprise": 6,
                },
                "idx_to_label": {
                    0: "anger",
                    1: "disgust",
                    2: "fear",
                    3: "happiness",
                    4: "neutral",
                    5: "sadness",
                    6: "surprise",
                },
            },
            "sub_emotion": {
                "classes_": [
                    "admiration",
                    "amusement",
                    "anger",
                    "annoyance",
                    "approval",
                    "aversion",
                    "caring",
                    "confusion",
                    "curiosity",
                    "desire",
                    "disappointment",
                    "disapproval",
                    "disgust",
                    "embarrassment",
                    "excitement",
                    "fear",
                    "gratitude",
                    "grief",
                    "joy",
                    "love",
                    "melancholy",
                    "nervousness",
                    "neutral",
                    "optimism",
                    "pride",
                    "realization",
                    "relief",
                    "remorse",
                    "sadness",
                    "surprise",
                ],
                "label_to_idx": {
                    "admiration": 0,
                    "amusement": 1,
                    "anger": 2,
                    "annoyance": 3,
                    "approval": 4,
                    "aversion": 5,
                    "caring": 6,
                    "confusion": 7,
                    "curiosity": 8,
                    "desire": 9,
                    "disappointment": 10,
                    "disapproval": 11,
                    "disgust": 12,
                    "embarrassment": 13,
                    "excitement": 14,
                    "fear": 15,
                    "gratitude": 16,
                    "grief": 17,
                    "joy": 18,
                    "love": 19,
                    "melancholy": 20,
                    "nervousness": 21,
                    "neutral": 22,
                    "optimism": 23,
                    "pride": 24,
                    "realization": 25,
                    "relief": 26,
                    "remorse": 27,
                    "sadness": 28,
                    "surprise": 29,
                },
                "idx_to_label": {
                    0: "admiration",
                    1: "amusement",
                    2: "anger",
                    3: "annoyance",
                    4: "approval",
                    5: "aversion",
                    6: "caring",
                    7: "confusion",
                    8: "curiosity",
                    9: "desire",
                    10: "disappointment",
                    11: "disapproval",
                    12: "disgust",
                    13: "embarrassment",
                    14: "excitement",
                    15: "fear",
                    16: "gratitude",
                    17: "grief",
                    18: "joy",
                    19: "love",
                    20: "melancholy",
                    21: "nervousness",
                    22: "neutral",
                    23: "optimism",
                    24: "pride",
                    25: "realization",
                    26: "relief",
                    27: "remorse",
                    28: "sadness",
                    29: "surprise",
                },
            },
            "intensity": {
                "classes_": ["mild", "moderate", "strong"],
                "label_to_idx": {"mild": 0, "moderate": 1, "strong": 2},
                "idx_to_label": {0: "mild", 1: "moderate", 2: "strong"},
            },
        }

        class HardcodedLabelEncoder:
            """Fallback label encoder using hardcoded mappings."""

            def __init__(self, encoder_data):
                self.classes_ = encoder_data["classes_"]
                self.label_to_idx = encoder_data["label_to_idx"]
                self.idx_to_label = encoder_data["idx_to_label"]

            def inverse_transform(self, indices):
                """Convert indices back to labels."""
                return [self.idx_to_label.get(idx, "unknown") for idx in indices]

            def transform(self, labels):
                """Convert labels to indices."""
                return [self.label_to_idx.get(label, -1) for label in labels]

        encoder_files = {
            "emotion": f"{self.encoders_dir}/emotion_encoder.pkl",
            "sub_emotion": f"{self.encoders_dir}/sub_emotion_encoder.pkl",
            "intensity": f"{self.encoders_dir}/intensity_encoder.pkl",
        }

        for encoder_name, file_path in encoder_files.items():
            try:
                with open(file_path, "rb") as f:
                    encoder = pickle.load(f)
                    setattr(self, f"{encoder_name}_encoder", encoder)
                    logger.info(f"✅ Loaded {encoder_name} encoder from {file_path}")
            except (pickle.UnpicklingError, EOFError, ValueError) as e:
                logger.error(f"❌ Corrupted encoder file detected: {file_path} - {e}")
                logger.warning(f"🗑️  Removing corrupted file: {file_path}")
                try:
                    os.remove(file_path)
                    logger.info(f"✅ Removed corrupted encoder: {file_path}")
                except OSError as remove_error:
                    logger.warning(
                        f"⚠️  Could not remove corrupted file: {remove_error}"
                    )

                # Use hardcoded fallback
                logger.info(f"🔄 Using hardcoded fallback for {encoder_name} encoder")
                fallback_encoder = HardcodedLabelEncoder(
                    HARDCODED_ENCODERS[encoder_name]
                )
                setattr(self, f"{encoder_name}_encoder", fallback_encoder)
                logger.info(f"✅ Hardcoded {encoder_name} encoder loaded successfully")

            except FileNotFoundError:
                logger.warning(f"⚠️  Encoder file not found: {file_path}")
                logger.info(f"🔄 Using hardcoded fallback for {encoder_name} encoder")
                fallback_encoder = HardcodedLabelEncoder(
                    HARDCODED_ENCODERS[encoder_name]
                )
                setattr(self, f"{encoder_name}_encoder", fallback_encoder)
                logger.info(f"✅ Hardcoded {encoder_name} encoder loaded successfully")

            except Exception as e:
                logger.error(f"❌ Failed to load {encoder_name} encoder: {e}")
                logger.info(f"🔄 Using hardcoded fallback for {encoder_name} encoder")
                fallback_encoder = HardcodedLabelEncoder(
                    HARDCODED_ENCODERS[encoder_name]
                )
                setattr(self, f"{encoder_name}_encoder", fallback_encoder)
                logger.info(f"✅ Hardcoded {encoder_name} encoder loaded successfully")

    def get_prediction(self, text):
        """
        Send a request to the Azure endpoint and return the raw response.
        """
        data = {"text": text}
        body = str.encode(json.dumps(data))
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }
        req = urllib.request.Request(self.endpoint_url, body, headers)
        try:
            response = urllib.request.urlopen(req)
            result = response.read()
            return json.loads(result.decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise RuntimeError(
                f"Request failed: {error.code} {error.read().decode('utf8', 'ignore')}"
            )

    def decode_and_postprocess(self, raw_predictions):
        """
        Decode raw predictions and post-process sub-emotion to ensure consistency.
        """
        # Defensive: handle both logits and index predictions
        try:
            # If predictions are logits, take argmax
            if isinstance(raw_predictions.get("emotion"), (list, np.ndarray)):
                # The raw_predictions are nested inside another list,
                # so we take the first element [0]
                emotion_idx = int(np.argmax(raw_predictions["emotion"][0]))
            else:
                emotion_idx = int(raw_predictions["emotion"])
            if isinstance(raw_predictions.get("sub_emotion"), (list, np.ndarray)):
                # The raw_predictions are nested inside another list,
                #  so we take the first element [0]
                sub_emotion_logits = np.array(raw_predictions["sub_emotion"][0])
                # Will post-process below
            else:
                sub_emotion_logits = None
                sub_emotion_idx = int(raw_predictions["sub_emotion"])
            if isinstance(raw_predictions.get("intensity"), (list, np.ndarray)):
                # The raw_predictions are nested inside another list, so we
                #  take the first element [0]
                intensity_idx = int(np.argmax(raw_predictions["intensity"][0]))
            else:
                intensity_idx = int(raw_predictions["intensity"])
        except Exception as e:
            raise ValueError(f"Malformed raw predictions: {e}")

        # Decode main emotion
        emotion = self.emotion_encoder.inverse_transform([emotion_idx])[0]

        # Post-process sub-emotion: only allow sub-emotions that map to
        #  the predicted emotion
        if sub_emotion_logits is not None:
            sub_emotion_classes = self.sub_emotion_encoder.classes_
            # Get valid sub-emotion indices for this emotion
            valid_indices = [
                i
                for i, label in enumerate(sub_emotion_classes)
                if self.emotion_mapping.get(label) == emotion
            ]
            if valid_indices:
                # Pick the valid sub-emotion with highest logit
                best_idx = valid_indices[np.argmax(sub_emotion_logits[valid_indices])]
                sub_emotion = sub_emotion_classes[best_idx]
            else:
                # Fallback: pick the most probable sub-emotion
                sub_emotion = self.sub_emotion_encoder.inverse_transform(
                    [int(np.argmax(sub_emotion_logits))]
                )[0]
        else:
            # If only index is given, just decode
            sub_emotion = self.sub_emotion_encoder.inverse_transform([sub_emotion_idx])[
                0
            ]
            # Optionally, check mapping and fallback if not valid
            if self.emotion_mapping.get(sub_emotion) != emotion:
                # Fallback: pick first valid sub-emotion for this emotion
                sub_emotion_classes = self.sub_emotion_encoder.classes_
                valid_labels = [
                    label
                    for label in sub_emotion_classes
                    if self.emotion_mapping.get(label) == emotion
                ]
                if valid_labels:
                    sub_emotion = valid_labels[0]

        # Decode intensity
        intensity = self.intensity_encoder.inverse_transform([intensity_idx])[0]

        return {"emotion": emotion, "sub_emotion": sub_emotion, "intensity": intensity}

    def predict(self, text: str) -> dict:
        """
        Full workflow: get prediction, decode, and post-process.
        Handles double-encoded JSON from the API.
        """
        max_retry = 5
        payload_dict = None
        output = None
        last_error = None

        for retry_count in range(max_retry):
            try:
                logger.info(
                    f"🔄 Attempt {retry_count + 1}/{max_retry} - Sending \
                        request to: {self.endpoint_url}"
                )

                # 1. Get the initial response from the API
                # (which is a string containing JSON)
                api_response_string = self.get_prediction(text)

                # 2. Parse this string to get the actual dictionary payload
                payload_dict = json.loads(api_response_string)

                # 3. Check if the status is "success" first
                if payload_dict.get("status") != "success":
                    raise RuntimeError(f"API returned error status: {payload_dict}")

                # 4. Get raw prediction
                raw_predictions = payload_dict.get("raw_predictions")
                if not raw_predictions:
                    raise RuntimeError(
                        f"No raw_predictions in response: {payload_dict}"
                    )

                # 5. Now, pass the clean dictionary of predictions to be processed
                output = self.decode_and_postprocess(raw_predictions)

                # If we got here, everything worked
                logger.info("✅ Prediction successful!")
                return output

            except Exception as e:
                last_error = e
                logger.error(f"❌ Attempt {retry_count + 1} failed: {e}")
                if retry_count < max_retry - 1:
                    logger.info("🔄 Retrying in a moment...")
                continue

        # If we got here, all retries failed
        error_msg = f"All {max_retry} attempts failed. Last error: {last_error}"
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg)

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Predict emotions for multiple texts (sequential calls).

        Args:
            texts: List of input texts

        Returns:
            List of prediction results
        """
        results = []
        for i, text in enumerate(texts):
            try:
                logger.info(f"📝 Processing text {i+1}/{len(texts)}")
                result = self.predict(text)
                # Wrap the result in the expected format
                results.append(
                    {"status": "success", "predictions": result, "text_index": i}
                )
            except Exception as e:
                logger.error(f"❌ Failed to process text {i+1}: {e}")
                results.append({"status": "error", "error": str(e), "text_index": i})

        return results


def predict_emotions_local(
    video_url: str,
    model_path: str = "models/weights/baseline_weights.pt",
    config_path: str = "models/weights/model_config.json",
    use_stt: bool = False,
    chunk_size: int = 200,
) -> Dict[str, Any]:
    """
    Predict emotions using local model inference.

    Args:
        video_url: URL or path to video/audio file
        model_path: Path to model weights
        config_path: Path to model configuration
        use_stt: Whether to use speech-to-text for audio
        chunk_size: Text chunk size for processing

    Returns:
        Dictionary containing predictions and metadata
    """
    logger.info(f"🎬 Starting local emotion prediction for: {video_url}")

    try:
        # Extract transcript using the unified transcription function
        transcript_data = transcribe_youtube_url(video_url, use_stt=use_stt)

        if not transcript_data.get("text"):
            raise ValueError("No transcript text extracted")

        text = transcript_data["text"]
        logger.info(f"📄 Extracted transcript: {len(text)} characters")

        # Load model and configuration
        logger.info("🔧 Loading model configuration...")
        with open(config_path, "r") as f:
            config = json.load(f)

        # Initialize feature extractor with config from model
        logger.info("🔍 Initializing feature extractor...")
        feature_config = config.get(
            "feature_config",
            {
                "pos": False,
                "textblob": False,
                "vader": False,
                "tfidf": True,
                "emolex": True,
            },
        )

        # Determine EmoLex path
        emolex_path = None
        emolex_paths = [
            "models/features/EmoLex/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
            "models/features/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
        ]
        for path in emolex_paths:
            if os.path.exists(path):
                emolex_path = path
                break

        feature_extractor = FeatureExtractor(
            feature_config=feature_config, lexicon_path=emolex_path
        )

        # Fit TF-IDF vectorizer if enabled (required for TF-IDF features)
        if feature_config.get("tfidf", False):
            # For prediction, fit with more comprehensive text to get
            # proper TF-IDF dimensions
            # Use larger chunks to ensure we get the full 100 features expected
            text_chunks = [
                text[i : i + 2000] for i in range(0, min(len(text), 10000), 2000)
            ]
            if not text_chunks:
                text_chunks = [text[:2000] if text else "sample text for tfidf fitting"]
            feature_extractor.fit_tfidf(text_chunks)

        # Initialize model
        logger.info("🧠 Loading model...")
        model = DEBERTAClassifier(
            model_name=config["model_name"],
            feature_dim=config["feature_dim"],
            num_classes=config["num_classes"],
            hidden_dim=config["hidden_dim"],
            dropout=config["dropout"],
        )

        # Load weights
        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        state_dict = torch.load(model_path, map_location=device, weights_only=False)

        # Check if we need to remap BERT layer names to DeBERTa (compatibility fix)
        if any(key.startswith("bert.") for key in state_dict.keys()):
            logger.info("🔄 Detected BERT layer names, remapping to DeBERTa format...")
            state_dict = _remap_bert_to_deberta_state_dict(state_dict)

        model.load_state_dict(state_dict, strict=False)
        model.to(device)
        model.eval()

        # Process text in chunks with correct feature dimension
        expected_feature_dim = config.get("feature_dim", 121)
        predictions = process_text_chunks(
            text, model, feature_extractor, chunk_size, expected_feature_dim
        )

        result = {
            "predictions": predictions,
            "metadata": {
                "video_url": video_url,
                "transcript_length": len(text),
                "chunks_processed": len(predictions),
                "model_type": "local",
                "stt_used": use_stt,
            },
            "transcript_data": transcript_data,
        }

        logger.info("✅ Local emotion prediction completed successfully")
        return result

    except Exception as e:
        logger.error(f"❌ Local prediction failed: {e}")
        raise


def predict_emotions_azure(
    video_url: str,
    endpoint_url: Optional[str] = None,
    api_key: Optional[str] = None,
    use_stt: bool = False,
    chunk_size: int = 200,
    use_ngrok: Optional[bool] = None,
    server_ip: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Predict emotions using Azure ML endpoint with auto-loaded configuration.

    Args:
        video_url: URL or path to video/audio file
        endpoint_url: Azure ML endpoint URL (overrides .env if provided)
        api_key: Azure ML API key (overrides .env if provided)
        use_stt: Whether to use speech-to-text for audio
        chunk_size: Text chunk size for processing
        use_ngrok: Whether to use NGROK tunnel (overrides .env if provided)
        server_ip: Server IP for NGROK (overrides .env if provided)

    Returns:
        Dictionary containing predictions and metadata
    """
    logger.info(f"🌐 Starting Azure emotion prediction for: {video_url}")

    try:
        # Load Azure configuration with fallback to .env
        azure_config = get_azure_config(
            endpoint_url=endpoint_url,
            api_key=api_key,
            use_ngrok=use_ngrok,
            server_ip=server_ip,
        )

        # Extract transcript using the unified transcription function
        transcript_data = transcribe_youtube_url(video_url, use_stt=use_stt)

        if not transcript_data.get("text"):
            raise ValueError("No transcript text extracted")

        text = transcript_data["text"]
        logger.info(f"📄 Extracted transcript: {len(text)} characters")

        # Initialize Azure predictor with loaded config
        predictor = AzureEndpointPredictor(
            api_key=azure_config["api_key"],
            endpoint_url=azure_config["endpoint_url"],
            encoders_dir="models/encoders",
        )

        # Process text in chunks
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        logger.info(f"📦 Processing {len(chunks)} text chunks...")

        predictions = predictor.predict_batch(chunks)

        result = {
            "predictions": predictions,
            "metadata": {
                "video_url": video_url,
                "transcript_length": len(text),
                "chunks_processed": len(predictions),
                "model_type": "azure",
                "endpoint_url": predictor.endpoint_url,
                "stt_used": use_stt,
                "ngrok_used": azure_config.get("use_ngrok", False),
            },
            "transcript_data": transcript_data,
        }

        logger.info("✅ Azure emotion prediction completed successfully")
        return result

    except Exception as e:
        logger.error(f"❌ Azure prediction failed: {e}")
        raise


def process_text_chunks(
    text: str,
    model,
    feature_extractor: FeatureExtractor,
    chunk_size: int = 200,
    expected_feature_dim: int = 121,
) -> List[Dict[str, Any]]:
    """
    Process text in chunks for local model inference.

    Args:
        text: Input text to process
        model: Loaded model
        feature_extractor: Feature extractor instance
        chunk_size: Size of text chunks

    Returns:
        List of predictions for each chunk
    """
    import torch
    from transformers import AutoTokenizer

    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-xsmall")
    device = next(model.parameters()).device

    # Split text into chunks
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    predictions = []

    for i, chunk in enumerate(chunks):
        try:
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

            # Extract features with expected dimension
            features = feature_extractor.extract_all_features(
                chunk, expected_dim=expected_feature_dim
            )
            features_tensor = torch.tensor(features, device=device).unsqueeze(0)

            # Tokenize
            inputs = tokenizer(
                chunk,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Predict
            with torch.no_grad():
                outputs = model(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    features=features_tensor,
                )

            # Convert to serializable format
            chunk_predictions = {}
            for key, value in outputs.items():
                if torch.is_tensor(value):
                    chunk_predictions[key] = value.cpu().tolist()
                else:
                    chunk_predictions[key] = value

            predictions.append(
                {
                    "chunk_index": i,
                    "chunk_text": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "predictions": chunk_predictions,
                    "status": "success",
                }
            )

        except Exception as e:
            logger.error(f"❌ Failed to process chunk {i+1}: {e}")
            predictions.append(
                {
                    "chunk_index": i,
                    "chunk_text": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                    "error": str(e),
                    "status": "error",
                }
            )

    return predictions


if __name__ == "__main__":
    # Configure command-line interface for pipeline execution
    parser = argparse.ArgumentParser(
        description="Emotion Classification Pipeline - "
        "Extract and analyze emotions from YouTube videos",
        epilog="Example: python predict.py 'https://youtube.com/watch?v=...' "
        "--transcription_method whisper",
    )
    parser.add_argument(
        "youtube_url",
        type=str,
        help="YouTube video URL for emotion analysis",
    )
    parser.add_argument(
        "--transcription_method",
        type=str,
        default="assemblyAI",
        choices=["assemblyAI", "whisper"],
        help="Speech-to-text service: 'assemblyAI' (cloud) or 'whisper' (local)",
    )

    args = parser.parse_args()

    # Execute the complete pipeline workflow
    predictions = process_youtube_url_and_predict(
        youtube_url=args.youtube_url,
        transcription_method=args.transcription_method,
    )

    # Provide execution summary and user feedback
    if predictions:
        logger.info("Pipeline completed successfully. Sample predictions:")
        # Display first 5 results as preview
        for i, pred in enumerate(predictions[:5]):
            logger.info(f"  Segment {i+1}: {pred}")
        logger.info(f"Total segments processed: {len(predictions)}")
    else:
        logger.warning("Pipeline completed but no predictions were generated.")
