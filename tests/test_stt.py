"""
Unit tests for emotion_clf_pipeline.stt module.

Tests speech-to-text functionality including transcription and audio processing.
"""

import unittest
from unittest.mock import MagicMock, patch

from emotion_clf_pipeline.stt import (
    SpeechToTextTranscriber,
    WhisperTranscriber,
    sanitize_filename,
)


class TestSanitizeFilename(unittest.TestCase):
    """Test cases for sanitize_filename function."""

    def test_sanitize_basic_filename(self):
        """Test sanitizing a basic filename."""
        result = sanitize_filename("test_file.txt")
        self.assertEqual(result, "test_file.txt")

    def test_sanitize_filename_with_invalid_chars(self):
        """Test sanitizing filename with invalid characters."""
        result = sanitize_filename("test<>:|?*file.txt")
        self.assertEqual(result, "test_file.txt")

    def test_sanitize_empty_filename(self):
        """Test sanitizing empty filename."""
        result = sanitize_filename("")
        self.assertEqual(result, "untitled")

    def test_sanitize_none_filename(self):
        """Test sanitizing None filename."""
        result = sanitize_filename(None)
        self.assertEqual(result, "untitled")

    def test_sanitize_long_filename(self):
        """Test sanitizing very long filename."""
        long_name = "a" * 250 + ".txt"
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 200)
        self.assertTrue(result.endswith(".txt"))

    def test_sanitize_reserved_name(self):
        """Test sanitizing Windows reserved names."""
        result = sanitize_filename("CON.txt")
        self.assertEqual(result, "_CON.txt")


class TestSpeechToTextTranscriber(unittest.TestCase):
    """Test cases for SpeechToTextTranscriber class."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.object(SpeechToTextTranscriber, '_setup_assemblyai'):
            self.transcriber = SpeechToTextTranscriber("test_api_key")

    def test_init(self):
        """Test SpeechToTextTranscriber initialization."""
        self.assertEqual(self.transcriber.api_key, "test_api_key")

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        result = self.transcriber._format_timestamp(3661.5)
        # Should format to HH:MM:SS
        self.assertRegex(result, r'\d{1,2}:\d{2}:\d{2}')

    @patch('os.path.exists')
    @patch('assemblyai.Transcriber')
    def test_transcribe_audio_success(self, mock_transcriber_class, mock_exists):
        """Test successful audio transcription."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock AssemblyAI components
        mock_transcript = MagicMock()
        mock_transcript.status = 'completed'  # Simulate successful status
        mock_transcript.text = "This is a test transcription"
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = mock_transcript
        mock_transcriber_class.return_value = mock_transcriber
        
        result = self.transcriber.transcribe_audio("test_audio.wav")
        
        self.assertEqual(result, mock_transcript)

    @patch('os.path.exists')
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test transcription with missing file."""
        mock_exists.return_value = False
        
        with self.assertRaises(FileNotFoundError):
            self.transcriber.transcribe_audio("nonexistent.wav")

    @patch('pandas.DataFrame.to_csv')
    @patch('pandas.DataFrame.to_excel')
    def test_save_transcript_csv(self, mock_to_excel, mock_to_csv):
        """Test saving transcript to CSV."""
        # Mock transcript with sentences
        mock_transcript = MagicMock()
        mock_sentence = MagicMock()
        mock_sentence.text = "Test sentence"
        mock_sentence.start = 1000  # milliseconds
        mock_sentence.end = 2000    # milliseconds
        mock_transcript.get_sentences.return_value = [mock_sentence]
        
        self.transcriber.save_transcript(mock_transcript, "output.csv")
        
        mock_to_csv.assert_called_once()
        mock_to_excel.assert_not_called()

    @patch('pandas.DataFrame.to_excel')
    def test_save_transcript_excel(self, mock_to_excel):
        """Test saving transcript to Excel."""
        # Mock transcript with sentences
        mock_transcript = MagicMock()
        mock_sentence = MagicMock()
        mock_sentence.text = "Test sentence"
        mock_sentence.start = 1000
        mock_sentence.end = 2000
        mock_transcript.get_sentences.return_value = [mock_sentence]
        
        self.transcriber.save_transcript(mock_transcript, "output.xlsx")
        
        mock_to_excel.assert_called_once()


class TestWhisperTranscriber(unittest.TestCase):
    """Test cases for WhisperTranscriber class."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('emotion_clf_pipeline.stt.check_cuda_status'):
            with patch('emotion_clf_pipeline.stt.whisper.load_model'):
                self.transcriber = WhisperTranscriber()

    def test_init(self):
        """Test WhisperTranscriber initialization."""
        self.assertEqual(self.transcriber.model_size, "base")
        self.assertIsNotNone(self.transcriber.device)

    def test_get_device_cuda_available(self):
        """Test device selection with CUDA available."""
        with patch('torch.cuda.is_available', return_value=True):
            device = self.transcriber._get_device()
            self.assertEqual(device, "cuda")

    def test_get_device_cpu_only(self):
        """Test device selection with CPU only."""
        with patch('torch.cuda.is_available', return_value=False):
            device = self.transcriber._get_device()
            self.assertEqual(device, "cpu")

    def test_get_device_force_cpu(self):
        """Test forcing CPU device."""
        transcriber = WhisperTranscriber(force_cpu=True)
        # The constructor should set device to CPU regardless of CUDA availability
        self.assertEqual(transcriber.device, "cpu")

    @patch('os.path.exists')
    @patch('emotion_clf_pipeline.stt.whisper.load_model')
    def test_transcribe_audio_success(self, mock_load_model, mock_exists):
        """Test successful Whisper transcription."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock Whisper model
        mock_model = MagicMock()
        mock_result = {
            'text': 'This is a test transcription',
            'segments': [
                {
                    'start': 0.0,
                    'end': 1.0,
                    'text': 'This is a test'
                }
            ]
        }
        mock_model.transcribe.return_value = mock_result
        self.transcriber.model = mock_model
        
        result = self.transcriber.transcribe_audio("test_audio.wav")
        
        self.assertEqual(result, mock_result)

    @patch('os.path.exists')
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test transcription with missing file."""
        mock_exists.return_value = False
        
        with self.assertRaises(FileNotFoundError):
            self.transcriber.transcribe_audio("nonexistent.wav")

    def test_format_timestamp_static(self):
        """Test static timestamp formatting method."""
        result = WhisperTranscriber.format_timestamp(3661.5)
        self.assertRegex(result, r'\d{1,2}:\d{2}:\d{2}')

    def test_extract_sentences(self):
        """Test sentence extraction from Whisper result."""
        mock_result = {
            'segments': [
                {'start': 0.0, 'end': 2.0, 'text': ' First sentence. '},
                {'start': 2.0, 'end': 4.0, 'text': ' Second sentence. '},
            ]
        }
        
        sentences = self.transcriber.extract_sentences(mock_result)
        
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0]['Sentence'], 'First sentence.')
        self.assertEqual(sentences[1]['Sentence'], 'Second sentence.')

    @patch('pandas.DataFrame.to_csv')
    @patch('pandas.DataFrame.to_excel')
    def test_save_transcript_static_csv(self, mock_to_excel, mock_to_csv):
        """Test static save_transcript method with CSV."""
        transcript_data = [
            {'Sentence': 'Test sentence', 'Start Time': '00:00:00', 'End Time': '00:00:02'}
        ]
        
        WhisperTranscriber.save_transcript(transcript_data, "output.csv")
        
        mock_to_csv.assert_called_once()

    @patch('pandas.DataFrame.to_excel')
    def test_save_transcript_static_excel(self, mock_to_excel):
        """Test static save_transcript method with Excel."""
        transcript_data = [
            {'Sentence': 'Test sentence', 'Start Time': '00:00:00', 'End Time': '00:00:02'}
        ]
        
        WhisperTranscriber.save_transcript(transcript_data, "output.xlsx")
        
        mock_to_excel.assert_called_once()


if __name__ == '__main__':
    unittest.main() 