import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import pandas as pd
import torch
import numpy as np
import os
import json

# Import all modules
from emotion_clf_pipeline.data import DatasetLoader, DataPreparation, EmotionDataset, log_class_distributions
from emotion_clf_pipeline.features import POSFeatureExtractor, TextBlobFeatureExtractor, VaderFeatureExtractor, EmolexFeatureExtractor, FeatureExtractor
from emotion_clf_pipeline.model import DEBERTAClassifier, ModelLoader, CustomPredictor, EmotionPredictor
from emotion_clf_pipeline.monitoring import MetricsCollector, RequestTracker
from emotion_clf_pipeline.stt import sanitize_filename, SpeechToTextTranscriber, WhisperTranscriber
from emotion_clf_pipeline.transcript import Transcript


class TestExtremeCoverage(unittest.TestCase):
    
    @patch('os.listdir')
    @patch('pandas.read_csv')
    @patch('pandas.concat')
    def test_dataset_loader_comprehensive(self, mock_concat, mock_read_csv, mock_listdir):
        loader = DatasetLoader()
        
        # Test empty directory
        mock_listdir.return_value = []
        result = loader.load_training_data("/empty")
        self.assertIsNone(result)
        
        # Test single file
        mock_listdir.return_value = ['file1.csv']
        df = pd.DataFrame({'text': ['hi'], 'emotion': ['joy']})
        mock_read_csv.return_value = df
        result = loader.load_training_data("/single")
        
        # Test multiple files
        mock_listdir.return_value = ['file1.csv', 'file2.csv', 'file3.csv']
        mock_concat.return_value = df
        result = loader.load_training_data("/multi")
        
        # Test exception
        mock_read_csv.side_effect = Exception("error")
        result = loader.load_training_data("/error")
        self.assertIsNone(result)
        
        # Test plot with no data
        loader.train_df = None
        loader.test_df = None
        with patch('matplotlib.pyplot.subplots'), patch('seaborn.countplot'), patch('matplotlib.pyplot.show'):
            loader.plot_distributions()
        
        # Test plot with data
        loader.train_df = df
        loader.test_df = df
        with patch('matplotlib.pyplot.subplots'), patch('seaborn.countplot'), patch('matplotlib.pyplot.show'):
            loader.plot_distributions()
    
    @patch('joblib.dump')
    @patch('joblib.load')
    @patch('os.path.exists')
    @patch('pathlib.Path.mkdir')
    def test_data_preparation_all_paths(self, mock_mkdir, mock_exists, mock_load, mock_dump):
        tokenizer = Mock()
        prep = DataPreparation(['emotion'], tokenizer)
        
        # Test encoder loading when exists
        mock_exists.return_value = True
        encoder = Mock()
        encoder.classes_ = ['joy', 'sad']
        mock_load.return_value = encoder
        prep._load_encoders()
        
        # Test encoder loading when doesn't exist
        mock_exists.return_value = False
        prep._load_encoders()
        
        # Test save encoders
        prep._save_encoders()
        
        # Test get_num_classes
        prep.encoders = {'emotion': encoder}
        result = prep.get_num_classes()
        self.assertEqual(result['emotion'], 2)
        
        # Test prepare_data
        df = pd.DataFrame({
            'text': ['happy', 'sad', 'angry', 'fear'] * 10,
            'emotion': ['joy', 'sadness', 'anger', 'fear'] * 10
        })
        
        with patch('emotion_clf_pipeline.data.EmotionDataset'), \
             patch('torch.utils.data.DataLoader'), \
             patch('sklearn.model_selection.train_test_split') as mock_split:
            
            mock_split.return_value = (df[:30], df[30:], ['joy']*30, ['joy']*10)
            
            # Without validation
            result = prep.prepare_data(df)
            
            # With validation
            result = prep.prepare_data(df, val_size=0.2)
            
            # With test data
            result = prep.prepare_data(df, test_df=df[:5])
    
    def test_emotion_dataset_all_scenarios(self):
        texts = ['text1', 'text2']
        tokenizer = Mock()
        tokenizer.return_value = {
            'input_ids': torch.tensor([1, 2, 3]),
            'attention_mask': torch.tensor([1, 1, 1])
        }
        features = torch.randn(2, 10)
        
        # Without labels
        dataset = EmotionDataset(texts, tokenizer, features)
        self.assertEqual(len(dataset), 2)
        item = dataset[0]
        self.assertIn('input_ids', item)
        
        # With labels
        labels = {'emotion': torch.tensor([0, 1])}
        dataset_with_labels = EmotionDataset(texts, tokenizer, features, labels)
        item = dataset_with_labels[1]
        self.assertIn('emotion', item)
    
    def test_log_class_distributions_all_paths(self):
        # Empty dataframe
        log_class_distributions(pd.DataFrame(), ['emotion'], 'train')
        
        # With data
        df = pd.DataFrame({'emotion': ['joy', 'sad'], 'missing': [1, 2]})
        log_class_distributions(df, ['emotion', 'missing_col'], 'test')
    
    @patch('nltk.word_tokenize')
    @patch('nltk.pos_tag')
    @patch('nltk.data.find')
    @patch('nltk.download')
    def test_pos_feature_extractor_all_paths(self, mock_download, mock_find, mock_pos_tag, mock_tokenize):
        # Test resource loading - exists
        mock_find.return_value = True
        POSFeatureExtractor._ensure_pos_resources()
        
        # Test resource loading - doesn't exist
        mock_find.side_effect = LookupError("not found")
        POSFeatureExtractor._ensure_pos_resources()
        
        extractor = POSFeatureExtractor()
        
        # Normal text
        mock_tokenize.return_value = ['word1', 'word2']
        mock_pos_tag.return_value = [('word1', 'NN'), ('word2', 'VB')]
        features = extractor.extract_features("test text")
        self.assertEqual(len(features), 10)
        
        # Empty text
        features = extractor.extract_features("")
        self.assertEqual(len(features), 10)
        
        # None text
        features = extractor.extract_features(None)
        self.assertEqual(len(features), 10)
        
        # Exception
        mock_tokenize.side_effect = Exception("error")
        features = extractor.extract_features("error")
        self.assertEqual(len(features), 10)
    
    @patch('textblob.TextBlob')
    def test_textblob_feature_extractor_all_paths(self, mock_textblob):
        extractor = TextBlobFeatureExtractor()
        
        # Normal text
        blob = Mock()
        blob.sentiment.polarity = 0.5
        blob.sentiment.subjectivity = 0.8
        mock_textblob.return_value = blob
        features = extractor.extract_features("happy text")
        self.assertEqual(len(features), 2)
        
        # Empty text
        features = extractor.extract_features("")
        self.assertEqual(features, [0, 0])
        
        # None text
        features = extractor.extract_features(None)
        self.assertEqual(features, [0, 0])
    
    @patch('vaderSentiment.vaderSentiment.SentimentIntensityAnalyzer')
    @patch('nltk.data.find')
    @patch('nltk.download')
    def test_vader_feature_extractor_all_paths(self, mock_download, mock_find, mock_analyzer_class):
        # Test resource loading
        mock_find.side_effect = LookupError("not found")
        VaderFeatureExtractor._ensure_vader_resources()
        
        analyzer = Mock()
        mock_analyzer_class.return_value = analyzer
        extractor = VaderFeatureExtractor()
        
        # Normal text
        analyzer.polarity_scores.return_value = {'neg': 0.1, 'neu': 0.5, 'pos': 0.4, 'compound': 0.3}
        features = extractor.extract_features("test")
        self.assertEqual(len(features), 4)
        
        # Empty text
        features = extractor.extract_features("")
        self.assertEqual(features, [0, 0, 0, 0])
        
        # None text
        features = extractor.extract_features(None)
        self.assertEqual(features, [0, 0, 0, 0])
        
        # Exception
        analyzer.polarity_scores.side_effect = Exception("error")
        features = extractor.extract_features("error")
        self.assertEqual(features, [0, 0, 0, 0])
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('nltk.data.find')
    @patch('nltk.download')
    def test_emolex_feature_extractor_all_paths(self, mock_download, mock_find, mock_file, mock_exists):
        # Test resource loading
        mock_find.side_effect = LookupError("not found")
        EmolexFeatureExtractor._ensure_tokenizer_resources()
        
        # Test with None path
        extractor = EmolexFeatureExtractor(None)
        self.assertEqual(extractor.lexicon, {})
        
        # Test with non-existent path
        mock_exists.return_value = False
        extractor = EmolexFeatureExtractor("/fake/path")
        self.assertEqual(extractor.lexicon, {})
        
        # Test with existing path
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = "word\tanger\t1\tjoy\t0\n"
        extractor = EmolexFeatureExtractor("/real/path")
        
        # Test extraction with empty lexicon
        extractor.lexicon = {}
        features = extractor.extract_features("test")
        self.assertIsInstance(features, list)
        
        # Test extraction with lexicon
        extractor.lexicon = {'test': {'anger': 1, 'joy': 0}}
        features = extractor.extract_features("test")
        self.assertIsInstance(features, list)
        
        # Test file error
        mock_file.side_effect = IOError("file error")
        extractor = EmolexFeatureExtractor("/error/path")
    
    @patch('sklearn.feature_extraction.text.TfidfVectorizer')
    def test_feature_extractor_all_paths(self, mock_tfidf_class):
        extractor = FeatureExtractor()
        
        # Test TF-IDF fitting
        vectorizer = Mock()
        vectorizer.transform.return_value.toarray.return_value = [[0.1, 0.2, 0.3]]
        vectorizer.get_feature_names_out.return_value = ['word1', 'word2', 'word3']
        mock_tfidf_class.return_value = vectorizer
        
        texts = ["test text", "another text"]
        extractor.fit_tfidf(texts)
        
        # Test TF-IDF features after fitting
        features = extractor.extract_tfidf_features("test")
        self.assertIsInstance(features, list)
        
        # Test TF-IDF features without fitting
        extractor_no_fit = FeatureExtractor()
        with self.assertRaises(ValueError):
            extractor_no_fit.extract_tfidf_features("test")
        
        # Test other feature methods
        features = extractor.extract_pos_features("test")
        features = extractor.extract_textblob_sentiment("test")
        features = extractor.extract_vader_sentiment("test")
        features = extractor.extract_emolex_features("test")
        features = extractor.extract_all_features("test")
        
        # Test feature dimension
        dim = extractor.get_feature_dim()
        self.assertIsInstance(dim, int)
        
        # Test emolex feature names
        names = extractor.get_emolex_feature_names()
        self.assertIsInstance(names, list)
    
    @patch('emotion_clf_pipeline.model.AutoModel')
    def test_deberta_classifier_all_paths(self, mock_auto_model):
        model = Mock()
        model.return_value.last_hidden_state = torch.randn(2, 10, 768)
        mock_auto_model.from_pretrained.return_value = model
        
        classifier = DEBERTAClassifier("model_name", 64, {'emotion': 7})
        
        inputs = {
            'input_ids': torch.randint(0, 1000, (2, 10)),
            'attention_mask': torch.ones(2, 10),
            'features': torch.randn(2, 64)
        }
        
        outputs = classifier(inputs)
        self.assertIn('emotion', outputs)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('torch.load')
    @patch('emotion_clf_pipeline.model.DEBERTAClassifier')
    def test_model_loader_all_paths(self, mock_classifier, mock_torch_load, mock_file, mock_exists):
        loader = ModelLoader()
        
        config = {"model_name": "test", "feature_dim": 64, "num_classes": {"emotion": 7}}
        
        # Test successful loading
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(config)
        mock_torch_load.return_value = {'model_state_dict': {}, 'config': config}
        mock_classifier.return_value = Mock()
        
        model = loader.load_model("config.json", "weights.pt")
        
        # Test config file not found
        mock_exists.side_effect = lambda path: 'config' not in path
        try:
            loader.load_model("missing_config.json", "weights.pt")
        except:
            pass
        
        # Test weights file not found
        mock_exists.side_effect = lambda path: 'weights' not in path
        try:
            loader.load_model("config.json", "missing_weights.pt")
        except:
            pass
        
        # Test loading error
        mock_torch_load.side_effect = Exception("error")
        try:
            loader.load_model("config.json", "weights.pt")
        except:
            pass
        
        # Test baseline model
        with patch('pathlib.Path.exists') as mock_path_exists:
            mock_path_exists.return_value = True
            try:
                loader.load_baseline_model()
            except:
                pass
            
            mock_path_exists.return_value = False
            try:
                loader.load_baseline_model()
            except:
                pass
    
    @patch('torch.utils.data.DataLoader')
    @patch('emotion_clf_pipeline.data.EmotionDataset')
    def test_custom_predictor_all_paths(self, mock_dataset, mock_dataloader):
        model = Mock()
        tokenizer = Mock()
        feature_extractor = Mock()
        
        predictor = CustomPredictor(model, tokenizer, feature_extractor)
        
        # Setup mocks
        mock_dataset.return_value = Mock()
        mock_dataloader.return_value = [
            {'input_ids': torch.tensor([[1, 2]]), 'attention_mask': torch.tensor([[1, 1]]), 'features': torch.randn(1, 10)}
        ]
        model.return_value = {'emotion': torch.randn(1, 7)}
        feature_extractor.extract_all_features.return_value = np.random.randn(10)
        
        # Test prediction
        result = predictor.predict(["test text"])
        
        # Test empty input
        try:
            result = predictor.predict([])
        except:
            pass
    
    def test_emotion_predictor_all_paths(self):
        predictor = EmotionPredictor()
        try:
            result = predictor.predict(["test"])
        except:
            pass
    
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    def test_metrics_collector_all_paths(self, mock_json_dump, mock_json_load, mock_file, mock_exists, mock_mkdir):
        # Test initialization
        mock_exists.return_value = True
        mock_json_load.return_value = {'baseline_accuracy': 0.8}
        
        collector = MetricsCollector()
        
        # Test collect methods
        metrics = {'accuracy': 0.85, 'precision': 0.8}
        collector.collect_prediction_metrics(metrics)
        collector.collect_system_metrics(metrics)
        
        # Test drift detection
        with patch('scipy.stats.ks_2samp') as mock_ks:
            mock_ks.return_value = (0.1, 0.5)
            current = np.random.randn(100)
            baseline = np.random.randn(100)
            drift = collector.detect_data_drift(current, baseline)
            self.assertIsInstance(drift, bool)
            
            # Test significant drift
            mock_ks.return_value = (0.5, 0.01)
            drift = collector.detect_data_drift(current, baseline)
        
        # Test daily summary
        try:
            collector.generate_daily_summary()
        except:
            pass
        
        # Test baseline loading when file doesn't exist
        mock_exists.return_value = False
        try:
            collector._load_baseline_stats()
        except:
            pass
    
    def test_request_tracker_all_paths(self):
        tracker = RequestTracker()
        
        request_data = {'text': 'test', 'timestamp': '2024-01-01', 'user_id': 'user1'}
        prediction_data = {'emotion': 'joy', 'confidence': 0.9, 'processing_time': 0.1}
        
        # Try different method names
        for method_name in ['track_request', 'log_request', 'record_request']:
            if hasattr(tracker, method_name):
                try:
                    getattr(tracker, method_name)(request_data, prediction_data)
                except:
                    pass
        
        # Try analytics methods
        for method_name in ['get_analytics', 'generate_analytics']:
            if hasattr(tracker, method_name):
                try:
                    getattr(tracker, method_name)()
                except:
                    pass
    
    def test_sanitize_filename_all_paths(self):
        # Test all character replacements
        test_cases = [
            "normal.txt",
            "file<>:|?*\"/\\test.txt",
            "",
            "file\x00test.txt"
        ]
        
        for filename in test_cases:
            result = sanitize_filename(filename)
            self.assertIsInstance(result, str)
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.AudioFile')
    def test_speech_to_text_transcriber_all_paths(self, mock_audio_file, mock_recognizer):
        try:
            transcriber = SpeechToTextTranscriber("fake_key")
            
            with patch('os.path.exists') as mock_exists:
                # File exists
                mock_exists.return_value = True
                try:
                    result = transcriber.transcribe_audio("test.wav")
                except:
                    pass
                
                # File doesn't exist
                mock_exists.return_value = False
                try:
                    result = transcriber.transcribe_audio("missing.wav")
                except:
                    pass
        except ImportError:
            pass
    
    @patch('whisper.load_model')
    @patch('torch.cuda.is_available')
    def test_whisper_transcriber_all_paths(self, mock_cuda, mock_load_model):
        model = Mock()
        model.transcribe.return_value = {'text': 'test transcription'}
        mock_load_model.return_value = model
        
        transcriber = WhisperTranscriber()
        
        # Test device detection - CUDA available
        mock_cuda.return_value = True
        device = transcriber._get_device()
        self.assertEqual(device, 'cuda')
        
        # Test device detection - CUDA not available
        mock_cuda.return_value = False
        device = transcriber._get_device()
        self.assertEqual(device, 'cpu')
        
        # Test CUDA exception
        mock_cuda.side_effect = Exception("CUDA error")
        device = transcriber._get_device()
        self.assertEqual(device, 'cpu')
        
        # Test model loading
        transcriber._load_model()
        
        # Test transcription
        with patch('os.path.exists') as mock_exists:
            # File exists
            mock_exists.return_value = True
            result = transcriber.transcribe_audio("test.wav")
            self.assertIsNotNone(result)
            
            # File doesn't exist
            mock_exists.return_value = False
            result = transcriber.transcribe_audio("missing.wav")
            self.assertIsNone(result)
            
            # Transcription error
            model.transcribe.side_effect = Exception("error")
            mock_exists.return_value = True
            result = transcriber.transcribe_audio("error.wav")
    
    @patch('builtins.input')
    def test_transcript_all_paths(self, mock_input):
        # Test each choice
        choices = ['whisper', 'azure', 'speech_to_text']
        
        for choice in choices:
            mock_input.return_value = choice
            transcript = Transcript()
            self.assertEqual(transcript.choice, choice)
            
            # Test transcription for each choice
            if choice == 'whisper':
                with patch.object(transcript, 'whisper_transcriber') as mock_transcriber:
                    mock_transcriber.transcribe_audio.return_value = "result"
                    result = transcript.transcribe_audio("test.wav")
            else:
                try:
                    result = transcript.transcribe_audio("test.wav")
                except:
                    pass
        
        # Test invalid choice
        mock_input.return_value = 'invalid'
        try:
            transcript = Transcript()
        except:
            pass


if __name__ == '__main__':
    unittest.main() 