"""
Unit tests for emotion_clf_pipeline.transcript module.

Tests transcript processing functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from emotion_clf_pipeline.transcript import Transcript


class TestTranscript(unittest.TestCase):
    """Test cases for Transcript class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock user input to avoid interactive prompts
        with patch('builtins.input', return_value='whisper'):
            self.transcript = Transcript()

    def test_init_whisper_choice(self):
        """Test Transcript initialization with whisper choice."""
        with patch('builtins.input', return_value='whisper'):
            transcript = Transcript()
            self.assertEqual(transcript.choice, 'whisper')

    def test_init_assembly_choice(self):
        """Test Transcript initialization with assembly choice."""
        with patch('builtins.input', return_value='assembly'):
            transcript = Transcript()
            self.assertEqual(transcript.choice, 'assembly')

    def test_seconds_to_hms(self):
        """Test seconds to HMS conversion."""
        result = self.transcript.seconds_to_hms(3661)
        # Should return a string representation of timedelta
        self.assertIsInstance(result, str)
        self.assertIn(':', result)

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.rename')
    @patch('pytubefix.YouTube')
    def test_download_youtube_audio(self, mock_youtube, mock_rename, mock_makedirs, mock_exists):
        """Test YouTube audio download."""
        # Mock the YouTube object and its methods
        mock_yt = MagicMock()
        mock_stream = MagicMock()
        mock_stream.download.return_value = '/path/to/downloaded/file.mp4'
        mock_yt.streams.filter.return_value.first.return_value = mock_stream
        mock_youtube.return_value = mock_yt
        
        # Mock os functions
        mock_exists.return_value = False  # Directory doesn't exist
        
        result = self.transcript.download_youtube_audio()
        
        # Verify methods were called
        mock_makedirs.assert_called()
        mock_rename.assert_called()
        self.assertIsInstance(result, str)

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.remove')
    @patch('whisper.load_model')
    def test_whisper_model(self, mock_load_model, mock_remove, mock_makedirs, mock_exists):
        """Test Whisper model transcription."""
        # Mock file operations
        mock_exists.side_effect = lambda path: 'transcript' not in path or path.endswith('transcript.csv')
        
        # Mock Whisper model
        mock_model = MagicMock()
        mock_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.0,
                    'text': 'Test transcription segment'
                }
            ]
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        # Mock file writing
        with patch('builtins.open', create=True):
            with patch('csv.writer') as mock_writer:
                mock_writer_instance = MagicMock()
                mock_writer.return_value = mock_writer_instance
                
                # Should not raise any exceptions
                self.transcript.whisper_model('/path/to/audio.mp3')
                
                # Verify CSV writer was used
                mock_writer.assert_called()

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.remove')
    @patch('assemblyai.Transcriber')
    def test_transcribe_audio_with_assemblyai(self, mock_transcriber_class, mock_remove, mock_makedirs, mock_exists):
        """Test AssemblyAI transcription."""
        # Mock file operations
        mock_exists.side_effect = lambda path: 'transcript' not in path or path.endswith('transcript.csv')
        
        # Mock AssemblyAI components
        mock_transcript = MagicMock()
        mock_sentence = MagicMock()
        mock_sentence.text = "Test sentence"
        mock_sentence.start = 1000  # milliseconds
        mock_sentence.end = 2000    # milliseconds
        mock_transcript.get_sentences.return_value = [mock_sentence]
        
        mock_transcriber = MagicMock()
        mock_transcriber.transcribe.return_value = mock_transcript
        mock_transcriber_class.return_value = mock_transcriber
        
        # Mock file writing
        with patch('builtins.open', create=True):
            with patch('csv.writer') as mock_writer:
                mock_writer_instance = MagicMock()
                mock_writer.return_value = mock_writer_instance
                
                # Should not raise any exceptions
                self.transcript.transcribe_audio_with_assemblyai('/path/to/audio.mp3')
                
                # Verify CSV writer was used
                mock_writer.assert_called()

    @patch.object(Transcript, 'download_youtube_audio')
    @patch.object(Transcript, 'whisper_model')
    def test_process_whisper(self, mock_whisper_model, mock_download):
        """Test process method with whisper choice."""
        mock_download.return_value = '/path/to/audio.mp3'
        
        # Should not raise any exceptions
        self.transcript.process()
        
        mock_download.assert_called_once()
        mock_whisper_model.assert_called_once_with('/path/to/audio.mp3')

    @patch.object(Transcript, 'download_youtube_audio')
    @patch.object(Transcript, 'transcribe_audio_with_assemblyai')
    def test_process_assembly(self, mock_assembly, mock_download):
        """Test process method with assembly choice."""
        # Set up transcript with assembly choice
        with patch('builtins.input', return_value='assembly'):
            transcript = Transcript()
        
        mock_download.return_value = '/path/to/audio.mp3'
        
        # Should not raise any exceptions
        transcript.process()
        
        mock_download.assert_called_once()
        mock_assembly.assert_called_once_with('/path/to/audio.mp3')

    @patch.object(Transcript, 'download_youtube_audio')
    def test_process_with_exception(self, mock_download):
        """Test process method with exception handling."""
        mock_download.side_effect = Exception("Test exception")
        
        # Should not raise any exceptions (should be caught and printed)
        self.transcript.process()
        
        mock_download.assert_called_once()


if __name__ == '__main__':
    unittest.main() 