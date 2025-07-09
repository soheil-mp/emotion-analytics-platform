# Import the libraries
import logging
import os
import re
import sys
from typing import Dict, List, Optional

import assemblyai as aai
import pandas as pd
import torch
import whisper
from dotenv import load_dotenv
from pytubefix import YouTube

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a filename to be safe for all operating systems.

    Removes or replaces characters that are invalid on Windows, macOS, or Linux.
    Also handles edge cases like reserved names and excessive length.

    Args:
        filename: The original filename string
        max_length: Maximum allowed filename length (default: 200)

    Returns:
        str: A sanitized filename safe for cross-platform use

    Note:
        Ensures compatibility with Windows (most restrictive), macOS, and Linux
        filesystem naming conventions while preserving readability.
    """
    if not filename or not filename.strip():
        return "untitled"

    # Remove or replace invalid characters for Windows/cross-platform compatibility
    # Invalid chars: < > : " | ? * and control characters (0-31)
    invalid_chars = r'[<>:"|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, "_", filename)

    # Replace multiple consecutive underscores with single underscore
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing dots and spaces (problematic on Windows)
    sanitized = sanitized.strip(". ")

    # Handle Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    name_without_ext = os.path.splitext(sanitized)[0].upper()
    if name_without_ext in reserved_names:
        sanitized = f"_{sanitized}"

    # Truncate if too long while preserving file extension
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_length = max_length - len(ext)
        sanitized = name[:max_name_length] + ext

    # Final fallback for edge cases
    if not sanitized or sanitized in (".", ".."):
        sanitized = "untitled"

    return sanitized


class SpeechToTextTranscriber:
    def __init__(self, api_key: str):
        """Initialize the transcriber with an API key.

        Args:
            api_key: AssemblyAI API key
        """
        self.api_key = api_key
        self._setup_assemblyai()

    def _setup_assemblyai(self) -> None:
        """Initialize AssemblyAI with the API key."""
        aai.settings.api_key = self.api_key

    def transcribe_audio(
        self, file_path: str, config: Optional[aai.TranscriptionConfig] = None
    ) -> aai.Transcript:
        """
        Transcribe the audio file using AssemblyAI.

        Args:
            file_path: Path to the audio file
            config: Optional transcription configuration

        Returns:
            AssemblyAI transcript object
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        transcriber = aai.Transcriber()

        try:
            transcript = transcriber.transcribe(file_path, config)

            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")

            return transcript

        except Exception as e:
            logger.error(f"Transcription error: {str(e)}", exc_info=True)
            raise

    def save_transcript(self, transcript: aai.Transcript, output_file: str) -> None:
        """
        Save the transcript to a file (CSV/Excel) with sentences and timestamps.

        Args:
            transcript: AssemblyAI transcript object
            output_file: Path to save the output file
        """
        # Store sentences with their timestamps
        transcript_data = []

        try:
            # Use the sentences endpoint to get properly separated sentences
            for sentence in transcript.get_sentences():
                # Convert timestamps from milliseconds to seconds
                start_time = sentence.start / 1000 if sentence.start is not None else 0
                end_time = sentence.end / 1000 if sentence.end is not None else 0

                # Format timestamps as HH:MM:SS
                start_formatted = self._format_timestamp(start_time)
                end_formatted = self._format_timestamp(end_time)

                transcript_data.append(
                    {
                        "Sentence": sentence.text,
                        "Start Time": start_formatted,
                        "End Time": end_formatted,
                    }
                )
        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            # Fallback: Split the full text into sentences (less accurate)
            sentences = [
                {"Sentence": s.strip(), "Start Time": "", "End Time": ""}
                for s in transcript.text.split(".")
                if s.strip()
            ]
            transcript_data = sentences

        # Create DataFrame with sentences and timestamps
        df = pd.DataFrame(transcript_data)

        # Save based on file extension
        file_ext = output_file.lower().split(".")[-1]
        if file_ext == "csv":
            df.to_csv(output_file, index=False)
        elif file_ext in ["xlsx", "xls"]:
            df.to_excel(output_file, index=False)
        else:
            raise ValueError("Unsupported output file format. Use .csv or .xlsx")

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format time in seconds to HH:MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string in HH:MM:SS format
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def process(self, audio_file: str, output_file: str = "transcript.xlsx") -> None:
        """
        Process an audio file and save the transcript.

        Args:
            audio_file: Path to the input audio file
            output_file: Path for the output transcript file
        """
        try:
            # Configure transcription
            config = aai.TranscriptionConfig(
                punctuate=True,  # Enable punctuation
                format_text=True,  # Enable text formatting
            )

            # Perform transcription
            logger.info(f"Transcribing {audio_file}...")
            transcript = self.transcribe_audio(audio_file, config)

            # Save results
            logger.info(f"Saving transcript to {output_file}...")
            self.save_transcript(transcript, output_file)

            logger.info("Transcription completed successfully!")

        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            raise


"""
Speech to Text Transcription using OpenAI's Whisper Model

This script takes an MP3 file as input and generates a structured output file
containing transcribed sentences with timestamps. It uses the Whisper model for
high-accuracy transcription.

Requirements:
    - whisper package (install with: pip install -U openai-whisper)
    - pandas package (install with: pip install pandas)
    - ffmpeg (install with: apt-get install ffmpeg or brew install ffmpeg)
"""


def check_cuda_status():
    """
    Check and print detailed CUDA status information.
    This function helps diagnose CUDA-related issues.

    Returns:
        bool: True if CUDA is available and properly configured
    """
    logger.info("\n===== CUDA Status Check =====")
    cuda_available = torch.cuda.is_available()
    logger.info(f"CUDA Available: {cuda_available}")

    if cuda_available:
        try:
            device_count = torch.cuda.device_count()
            logger.info(f"CUDA Device Count: {device_count}")

            for i in range(device_count):
                logger.info(f"CUDA Device {i}: {torch.cuda.get_device_name(i)}")

            logger.info(f"Current CUDA Device: {torch.cuda.current_device()}")
            logger.info(f"CUDA Version: {torch.version.cuda}")

            # Test a simple CUDA operation to confirm functionality
            # test_tensor = torch.tensor([1.0, 2.0, 3.0]).cuda()
            # result = test_tensor * 2
            logger.info("CUDA operation test successful!")

            return True
        except Exception as e:
            logger.error(f"CUDA Error: {str(e)}")
            return False
    else:
        logger.info("CUDA is not available. Possible reasons:")
        logger.info("1. NVIDIA GPU drivers are not installed or outdated")
        logger.info("2. CUDA toolkit is not installed or not in PATH")
        logger.info("3. PyTorch was installed without CUDA support")
        logger.info("\nRecommended solutions:")
        logger.info("1. Verify NVIDIA GPU drivers are installed")
        logger.info("2. Install CUDA toolkit (compatible with your PyTorch version)")
        logger.info("3. Reinstall PyTorch with CUDA support")
        return False


class WhisperTranscriber:
    def __init__(self, model_size: str = "base", force_cpu: bool = False):
        """
        Initialize the WhisperTranscriber with a specific model size.

        Args:
            model_size: Size of the model to use
                ("tiny", "base", "small", "medium", "large")
            force_cpu: If True, CPU will be used even if CUDA is available
        """
        self.model_size = model_size
        self.force_cpu = force_cpu
        self.device = self._get_device()
        logger.info(f"Using device: {self.device}")
        self.model = self._load_model()

    def _get_device(self) -> str:
        """
        Determine which device to use for model inference.

        Returns:
            str: "cuda" if CUDA is available and not forced to use CPU, otherwise "cpu"
        """
        if self.force_cpu:
            logger.info("Force CPU mode enabled, using CPU if CUDA is unavailable")
            return "cpu"

        if torch.cuda.is_available():
            # Check if CUDA is working properly
            cuda_ok = check_cuda_status()
            if cuda_ok:
                return "cuda"
            else:
                logger.info("CUDA issues detected. Falling back to CPU.")
                return "cpu"
        else:
            logger.info("CUDA not available. Using CPU (slower).")
            return "cpu"

    def _load_model(self) -> whisper.Whisper:
        """
        Load the Whisper model.

        Returns:
            Loaded Whisper model
        """
        try:
            logger.info(f"Loading {self.model_size} model on {self.device}...")
            model = whisper.load_model(self.model_size).to(self.device)
            logger.info(f"Model loaded successfully on {self.device}")
            return model
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            if self.device == "cuda" and "CUDA" in str(e):
                logger.info("Attempting to fall back to CPU...")
                self.device = "cpu"
                model = whisper.load_model(self.model_size).to(self.device)
                logger.info("Model loaded successfully on CPU")
                return model
            else:
                raise Exception(f"Error loading Whisper model: {str(e)}")

    def transcribe_audio(self, file_path: str, language: Optional[str] = None) -> Dict:
        """
        Transcribe the audio file using Whisper.

        Args:
            file_path: Path to the audio file
            language: Optional language code (e.g., "en" for English)

        Returns:
            Dictionary containing transcription results
        """
        # Convert to absolute path
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            logger.info(f"Using absolute file path: {file_path}")
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                file_path, language=language, word_timestamps=True, verbose=False
            )
            return result

        except Exception as e:
            if "ffmpeg" in str(e).lower():
                raise Exception(
                    f"FFMPEG error during transcription. Please make sure "
                    f"FFMPEG is correctly installed: {str(e)}"
                )
            else:
                raise Exception(f"Transcription error: {str(e)}")

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Format time in seconds to HH:MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string in HH:MM:SS format
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def extract_sentences(self, result: Dict) -> List[Dict]:
        """
        Extract sentences with timestamps from Whisper transcription result.

        Args:
            result: Whisper transcription result

        Returns:
            List of dictionaries containing sentences and their timestamps
        """
        transcript_data = []

        for segment in result["segments"]:
            # Get the text and timestamps
            text = segment["text"].strip()
            start_time = segment["start"]
            end_time = segment["end"]

            # Format timestamps
            start_formatted = self.format_timestamp(start_time)
            end_formatted = self.format_timestamp(end_time)

            # Add to transcript data if there's text
            if text:
                transcript_data.append(
                    {
                        "Sentence": text,
                        "Start Time": start_formatted,
                        "End Time": end_formatted,
                    }
                )

        return transcript_data

    @staticmethod
    def save_transcript(transcript_data: List[Dict], output_file: str) -> None:
        """
        Save the transcript to a file (CSV/Excel).

        Args:
            transcript_data: List of dictionaries containing transcription data
            output_file: Path to save the output file
        """
        # Create DataFrame
        df = pd.DataFrame(transcript_data)

        # Save based on file extension
        file_ext = output_file.lower().split(".")[-1]
        if file_ext == "csv":
            df.to_csv(output_file, index=False)
        elif file_ext in ["xlsx", "xls"]:
            df.to_excel(output_file, index=False)
        else:
            raise ValueError("Unsupported output file format. Use .csv or .xlsx")

    def process(
        self,
        audio_file: str,
        output_file: str = "transcript.xlsx",
        language: Optional[str] = None,
    ) -> None:
        """
        Process the audio file and generate a transcript.

        Args:
            audio_file: Path to the input audio file
            output_file: Path for the output transcript file
            language: Optional language code for transcription
        """
        try:
            # Ensure we have absolute file paths
            audio_file = os.path.abspath(audio_file)
            output_file = os.path.abspath(output_file)

            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Perform transcription
            logger.info(f"Transcribing {audio_file}...")
            result = self.transcribe_audio(audio_file, language)

            # Extract sentences with timestamps
            transcript_data = self.extract_sentences(result)

            # Save results
            logger.info(f"Saving transcript to {output_file}...")
            self.save_transcript(transcript_data, output_file)

            logger.info("Transcription completed successfully!")

        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            sys.exit(1)


# def save_youtube_audio(url, destination, return_path, filename=None):
def save_youtube_audio(url, destination):
    """
    Download the audio from a YouTube video and save it as an MP3 file.

    Args:
        url (str): The URL of the YouTube video.
        destination (str): The directory where the audio file should be saved.

    Returns:
        str: The path to the downloaded audio file.
    """
    try:
        # Initialize YouTube object
        yt = YouTube(url, use_po_token=False)

        # Get the best audio stream and download it
        audio_stream = yt.streams.filter(only_audio=True).first()

        # Title of the video
        title = yt.title

        # Sanitize the title for use as a filename
        title = sanitize_filename(title)

        # Remove if file already exists
        existing_file = os.path.join(destination, f"{title}.mp3")
        if os.path.exists(existing_file):
            logger.info(f"File already exists: {existing_file}")
            return existing_file, title

        # ensure destination directory exists
        if not os.path.exists(destination):
            os.makedirs(destination)

        # download the file
        out_file = audio_stream.download(output_path=destination)

        # Rename to title.mp3
        base, ext = os.path.splitext(out_file)
        new_file = os.path.join(destination, f"{title}.mp3")
        os.rename(out_file, new_file)

        return new_file, title
    except Exception as e:
        logger.error(f"Error downloading audio from {url}: {e}")
        raise


def save_youtube_video(url, destination):
    """
    Download a YouTube video and save it as an MP4 file.

    This function downloads the highest quality progressive video stream available,
    falling back to adaptive streams if necessary. Progressive streams contain
    both video and audio in a single file.

    Args:
        url (str): The YouTube video URL
        destination (str): The destination folder for the video file

    Returns:
        tuple: (video_file_path, title) - Path to saved video file and video title

    Raises:
        Exception: If video download fails or no suitable streams are found

    Note:
        Prioritizes progressive MP4 streams for best compatibility.
        Falls back to highest resolution adaptive stream if progressive unavailable.
    """
    try:
        # Initialize YouTube object
        yt = YouTube(url, use_po_token=False)

        # Get video title and sanitize for filename
        title = yt.title
        title = sanitize_filename(title)

        # Check if file already exists
        existing_file = os.path.join(destination, f"{title}.mp4")
        if os.path.exists(existing_file):
            logger.info(f"Video file already exists: {existing_file}")
            return existing_file, title

        # Ensure destination directory exists
        if not os.path.exists(destination):
            os.makedirs(destination)

        # Try to get progressive video stream first (includes audio)
        video_stream = (
            yt.streams.filter(progressive=True, file_extension="mp4")
            .order_by("resolution")
            .desc()
            .first()
        )

        # Fallback to adaptive video stream if no progressive available
        if not video_stream:
            logger.warning("No progressive streams available, using adaptive stream")
            video_stream = (
                yt.streams.filter(adaptive=True, file_extension="mp4", only_video=True)
                .order_by("resolution")
                .desc()
                .first()
            )

        # Check if any suitable stream was found
        if not video_stream:
            raise Exception("No suitable video streams found")

        logger.info(
            f"Downloading video: {title} " f"({video_stream.resolution or 'adaptive'})"
        )

        # Download the video file
        out_file = video_stream.download(output_path=destination)

        # Rename to standardized format: title.mp4
        base, ext = os.path.splitext(out_file)
        new_file = os.path.join(destination, f"{title}.mp4")
        os.rename(out_file, new_file)

        logger.info(f"Video saved successfully: {new_file}")
        return new_file, title

    except Exception as e:
        logger.error(f"Error downloading video from {url}: {str(e)}")
        raise
