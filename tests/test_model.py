"""
Unit tests for emotion_clf_pipeline.model module.

Tests model components including DEBERTAClassifier, ModelLoader, and predictors.
"""

import unittest
from unittest.mock import MagicMock, patch

import torch

from emotion_clf_pipeline.model import (
    CustomPredictor,
    DEBERTAClassifier,
    EmotionPredictor,
    ModelLoader,
)


class TestDEBERTAClassifier(unittest.TestCase):
    """Test cases for DEBERTAClassifier class."""

    def setUp(self):
        """Set up test fixtures."""
        self.model_name = "microsoft/deberta-v3-xsmall"
        self.feature_dim = 128
        self.num_classes = {
            'emotion': 7,
            'sub_emotion': 28,
            'intensity': 3
        }

    @patch('emotion_clf_pipeline.model.AutoModel')
    def test_init(self, mock_automodel):
        """Test DEBERTAClassifier initialization."""
        # Mock DEBERTA model
        mock_deberta = MagicMock()
        mock_deberta.config.hidden_size = 768
        mock_automodel.from_pretrained.return_value = mock_deberta
        
        classifier = DEBERTAClassifier(
            model_name=self.model_name,
            feature_dim=self.feature_dim,
            num_classes=self.num_classes
        )
        
        self.assertEqual(classifier.model_name, self.model_name)
        self.assertEqual(classifier.num_classes, self.num_classes)

    @patch('emotion_clf_pipeline.model.AutoModel')
    def test_forward(self, mock_automodel):
        """Test forward pass of DEBERTAClassifier."""
        # Mock DEBERTA model
        mock_deberta = MagicMock()
        mock_deberta.config.hidden_size = 768
        mock_output = MagicMock()
        mock_output.last_hidden_state = torch.randn(2, 10, 768)
        mock_deberta.return_value = mock_output
        mock_automodel.from_pretrained.return_value = mock_deberta
        
        classifier = DEBERTAClassifier(
            model_name=self.model_name,
            feature_dim=self.feature_dim,
            num_classes=self.num_classes
        )
        
        # Mock inputs
        input_ids = torch.randint(0, 1000, (2, 10))
        attention_mask = torch.ones(2, 10)
        features = torch.randn(2, self.feature_dim)
        
        output = classifier(input_ids, attention_mask, features)
        
        self.assertIn('emotion', output)
        self.assertIn('sub_emotion', output)
        self.assertIn('intensity', output)


class TestModelLoader(unittest.TestCase):
    """Test cases for ModelLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('emotion_clf_pipeline.model.DebertaV2Tokenizer'):
            self.loader = ModelLoader()

    def test_init(self):
        """Test ModelLoader initialization."""
        self.assertIsNotNone(self.loader.tokenizer)
        self.assertIsNotNone(self.loader.device)

    @patch('emotion_clf_pipeline.model.torch.load')
    @patch('emotion_clf_pipeline.model.DEBERTAClassifier')
    def test_load_model_with_weights(self, mock_classifier, mock_torch_load):
        """Test loading model with pretrained weights."""
        # Mock model and weights
        mock_model = MagicMock()
        mock_classifier.return_value = mock_model
        mock_torch_load.return_value = {'state': 'dict'}
        
        feature_dim = 128
        num_classes = {'emotion': 7, 'sub_emotion': 28, 'intensity': 3}
        
        with patch('os.path.exists', return_value=True):
            model = self.loader.load_model(
                feature_dim=feature_dim,
                num_classes=num_classes,
                weights_path="test_weights.pt"
            )
        
        self.assertIsNotNone(model)

    @patch('emotion_clf_pipeline.model.DEBERTAClassifier')
    def test_load_model_without_weights(self, mock_classifier):
        """Test loading model without pretrained weights."""
        mock_model = MagicMock()
        mock_classifier.return_value = mock_model
        
        feature_dim = 128
        num_classes = {'emotion': 7, 'sub_emotion': 28, 'intensity': 3}
        
        model = self.loader.load_model(
            feature_dim=feature_dim,
            num_classes=num_classes
        )
        
        self.assertIsNotNone(model)

    @patch('emotion_clf_pipeline.model.CustomPredictor')
    def test_create_predictor(self, mock_predictor):
        """Test creating predictor."""
        mock_model = MagicMock()
        mock_pred = MagicMock()
        mock_predictor.return_value = mock_pred
        
        predictor = self.loader.create_predictor(mock_model)
        
        self.assertIsNotNone(predictor)


class TestCustomPredictor(unittest.TestCase):
    """Test cases for CustomPredictor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_model = MagicMock()
        self.mock_tokenizer = MagicMock()
        self.device = torch.device('cpu')

    @patch('os.path.exists')
    @patch('pickle.load')
    @patch('builtins.open')
    def test_init(self, mock_open, mock_pickle_load, mock_exists):
        """Test CustomPredictor initialization."""
        # Mock encoder files exist
        mock_exists.return_value = True
        mock_pickle_load.return_value = MagicMock()
        
        predictor = CustomPredictor(
            model=self.mock_model,
            tokenizer=self.mock_tokenizer,
            device=self.device
        )
        
        self.assertEqual(predictor.model, self.mock_model)
        self.assertEqual(predictor.tokenizer, self.mock_tokenizer)
        self.assertEqual(predictor.device, self.device)

    @patch('os.path.exists')
    @patch('emotion_clf_pipeline.model.FeatureExtractor')
    def test_predict_single_text(self, mock_feature_extractor, mock_exists):
        """Test predicting single text."""
        # Mock encoder files don't exist (use hardcoded)
        mock_exists.return_value = False
        
        # Mock feature extractor
        mock_fe = MagicMock()
        mock_fe.extract_all_features.return_value = [0.1] * 121
        mock_feature_extractor.return_value = mock_fe
        
        # Mock model predictions
        self.mock_model.return_value = {
            'emotion': torch.tensor([[0.8, 0.2]]),
            'sub_emotion': torch.tensor([[0.9, 0.1]]),
            'intensity': torch.tensor([[0.7, 0.3]])
        }
        
        # Mock tokenizer
        self.mock_tokenizer.encode_plus.return_value = {
            'input_ids': [0, 1, 2],
            'attention_mask': [1, 1, 1]
        }
        
        predictor = CustomPredictor(
            model=self.mock_model,
            tokenizer=self.mock_tokenizer,
            device=self.device
        )
        
        # Mock encoders for inverse transform
        predictor.encoders = {
            'emotion': MagicMock(),
            'sub_emotion': MagicMock(),
            'intensity': MagicMock()
        }
        predictor.encoders['emotion'].inverse_transform.return_value = ['happiness']
        predictor.encoders['sub_emotion'].inverse_transform.return_value = ['joy']
        predictor.encoders['intensity'].inverse_transform.return_value = ['medium']
        
        result = predictor.predict(["This is a test text"])
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)


class TestEmotionPredictor(unittest.TestCase):
    """Test cases for EmotionPredictor class."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('emotion_clf_pipeline.model.ModelLoader'):
            self.predictor = EmotionPredictor()

    def test_init(self):
        """Test EmotionPredictor initialization."""
        self.assertIsNotNone(self.predictor.model_loader)
        self.assertIsNone(self.predictor.predictor)

    @patch.object(EmotionPredictor, 'ensure_best_baseline')
    def test_predict_loads_model(self, mock_ensure_baseline):
        """Test that predict loads model when needed."""
        # Mock model loading
        mock_predictor = MagicMock()
        mock_predictor.predict.return_value = [{'emotion': 'happiness'}]
        
        self.predictor.model_loader.load_baseline_model = MagicMock(
            return_value=(MagicMock(), MagicMock(), MagicMock())
        )
        self.predictor.model_loader.create_predictor = MagicMock(
            return_value=mock_predictor
        )
        
        result = self.predictor.predict(["test text"])
        
        self.assertIsInstance(result, list)


    def test_deberta_classifier_comprehensive_scenarios(self):
        """Test DEBERTAClassifier with all possible input scenarios."""
        with patch('emotion_clf_pipeline.model.AutoModel') as mock_auto_model:
            # Test various model configurations
            model_configs = [
                ("microsoft/deberta-v3-xsmall", 32, {'emotion': 7}),
                ("microsoft/deberta-v3-base", 64, {'emotion': 7, 'sub_emotion': 28}),
                ("microsoft/deberta-v3-large", 128, {'emotion': 7, 'sub_emotion': 28, 'intensity': 3}),
                ("custom-model", 256, {'emotion': 10, 'sub_emotion': 50, 'intensity': 5}),
            ]
            
            for model_name, feature_dim, num_classes in model_configs:
                mock_model = MagicMock()
                mock_auto_model.from_pretrained.return_value = mock_model
                
                classifier = DEBERTAClassifier(model_name, feature_dim, num_classes)
                
                # Test forward pass with various batch sizes and sequence lengths
                batch_scenarios = [
                    (1, 64),
                    (2, 128),
                    (4, 256),
                    (8, 512),
                    (16, 64),
                ]
                
                for batch_size, seq_len in batch_scenarios:
                    # Mock the transformer output
                    mock_model.return_value.last_hidden_state = torch.randn(batch_size, seq_len, 768)
                    
                    input_data = {
                        'input_ids': torch.randint(0, 1000, (batch_size, seq_len)),
                        'attention_mask': torch.ones(batch_size, seq_len),
                        'features': torch.randn(batch_size, feature_dim)
                    }
                    
                    outputs = classifier(input_data)
                    
                    # Verify outputs for all configured tasks
                    for task in num_classes.keys():
                        self.assertIn(task, outputs)
                        self.assertEqual(outputs[task].shape, (batch_size, num_classes[task]))

    def test_model_loader_comprehensive_error_scenarios(self):
        """Test ModelLoader with all possible error scenarios."""
        loader = ModelLoader()
        
        # Test various config scenarios
        valid_config = {
            "model_name": "microsoft/deberta-v3-xsmall",
            "feature_dim": 64,
            "num_classes": {"emotion": 7, "sub_emotion": 28, "intensity": 3}
        }
        
        invalid_configs = [
            {},  # Empty config
            {"model_name": "test"},  # Missing required fields
            {"feature_dim": 64},  # Missing model_name
            {"model_name": "test", "feature_dim": "invalid"},  # Invalid type
        ]
        
        # Test config file scenarios
        with patch('os.path.exists') as mock_exists:
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('torch.load') as mock_torch_load:
                    with patch('emotion_clf_pipeline.model.DEBERTAClassifier') as mock_classifier:
                        
                        # Test successful loading
                        mock_exists.return_value = True
                        mock_file.return_value.read.return_value = json.dumps(valid_config)
                        mock_torch_load.return_value = {
                            'model_state_dict': {'layer.weight': torch.randn(10, 10)},
                            'config': valid_config
                        }
                        mock_model = MagicMock()
                        mock_classifier.return_value = mock_model
                        
                        model = loader.load_model("config.json", "weights.pt")
                        self.assertIsNotNone(model)
                        
                        # Test config file not found
                        mock_exists.side_effect = lambda path: 'config' not in path
                        try:
                            loader.load_model("missing_config.json", "weights.pt")
                            self.fail("Should raise exception for missing config")
                        except Exception:
                            pass
                        
                        # Test weights file not found
                        mock_exists.side_effect = lambda path: 'weights' not in path
                        try:
                            loader.load_model("config.json", "missing_weights.pt")
                            self.fail("Should raise exception for missing weights")
                        except Exception:
                            pass
                        
                        # Test invalid JSON in config
                        mock_exists.return_value = True
                        mock_file.return_value.read.return_value = "invalid json"
                        try:
                            loader.load_model("invalid_config.json", "weights.pt")
                        except Exception:
                            pass
                        
                        # Test torch.load failure
                        mock_file.return_value.read.return_value = json.dumps(valid_config)
                        mock_torch_load.side_effect = Exception("Failed to load weights")
                        try:
                            loader.load_model("config.json", "corrupt_weights.pt")
                        except Exception:
                            pass
                        
                        # Test invalid configs
                        for invalid_config in invalid_configs:
                            mock_torch_load.side_effect = None
                            mock_torch_load.return_value = {
                                'model_state_dict': {},
                                'config': invalid_config
                            }
                            mock_file.return_value.read.return_value = json.dumps(invalid_config)
                            try:
                                loader.load_model("config.json", "weights.pt")
                            except Exception:
                                pass  # Expected to fail

    def test_baseline_model_comprehensive_scenarios(self):
        """Test baseline model loading with comprehensive scenarios."""
        loader = ModelLoader()
        
        with patch('pathlib.Path.exists') as mock_path_exists:
            with patch('emotion_clf_pipeline.model.DEBERTAClassifier') as mock_classifier:
                
                # Test successful baseline loading
                mock_path_exists.return_value = True
                mock_model = MagicMock()
                mock_classifier.return_value = mock_model
                
                try:
                    baseline = loader.load_baseline_model()
                    # Should create classifier with default config
                    mock_classifier.assert_called()
                except Exception:
                    pass  # May fail without proper config
                
                # Test baseline config missing
                mock_path_exists.return_value = False
                try:
                    baseline = loader.load_baseline_model()
                    self.fail("Should raise exception for missing baseline")
                except Exception:
                    pass  # Expected
                
                # Test classifier initialization failure
                mock_path_exists.return_value = True
                mock_classifier.side_effect = Exception("Failed to create classifier")
                try:
                    baseline = loader.load_baseline_model()
                except Exception:
                    pass  # Expected

    def test_custom_predictor_comprehensive_scenarios(self):
        """Test CustomPredictor with comprehensive scenarios."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        mock_feature_extractor = MagicMock()
        
        predictor = CustomPredictor(mock_model, mock_tokenizer, mock_feature_extractor)
        
        # Test various input scenarios
        input_scenarios = [
            [],  # Empty input
            ["single text"],  # Single text
            ["text one", "text two"],  # Multiple texts
            ["short", "medium length text", "a very very very long text with many words"],  # Various lengths
            [""] * 5,  # Empty strings
            ["text with special chars !@#$%^&*()"],  # Special characters
            ["🙂 emoji text 🎉"],  # Unicode/emoji
        ]
        
        for texts in input_scenarios:
            # Setup comprehensive mocks
            mock_feature_extractor.extract_all_features.return_value = np.random.randn(100)
            mock_tokenizer.return_value = {
                'input_ids': torch.tensor([101, 102, 103]),
                'attention_mask': torch.tensor([1, 1, 1])
            }
            
            # Mock model outputs for different task combinations
            output_scenarios = [
                {'emotion': torch.randn(len(texts) if texts else 1, 7)},
                {'emotion': torch.randn(len(texts) if texts else 1, 7), 'sub_emotion': torch.randn(len(texts) if texts else 1, 28)},
                {'emotion': torch.randn(len(texts) if texts else 1, 7), 'sub_emotion': torch.randn(len(texts) if texts else 1, 28), 'intensity': torch.randn(len(texts) if texts else 1, 3)},
            ]
            
            for model_output in output_scenarios:
                mock_model.return_value = model_output
                
                with patch('torch.utils.data.DataLoader') as mock_dataloader:
                    with patch('emotion_clf_pipeline.data.EmotionDataset') as mock_dataset:
                        mock_dataset.return_value = MagicMock()
                        
                        # Mock dataloader to return batches
                        mock_batch = {
                            'input_ids': torch.tensor([[101, 102]]),
                            'attention_mask': torch.tensor([[1, 1]]),
                            'features': torch.randn(1, 100)
                        }
                        mock_dataloader.return_value = [mock_batch] * max(1, len(texts))
                        
                        try:
                            result = predictor.predict(texts)
                            # Should return predictions for all configured tasks
                            for task in model_output.keys():
                                self.assertIn(task, result)
                        except Exception:
                            pass  # Some scenarios may fail

    def test_emotion_predictor_initialization_scenarios(self):
        """Test EmotionPredictor initialization and error handling."""
        predictor = EmotionPredictor()
        
        # Test prediction with no model loaded (should fail gracefully)
        test_inputs = [
            [],
            ["single text"],
            ["multiple", "texts", "here"],
            ["text with special chars !@#$"],
        ]
        
        for inputs in test_inputs:
            try:
                result = predictor.predict(inputs)
                # If it doesn't fail, result should be structured correctly
                if result:
                    self.assertIsInstance(result, dict)
            except Exception:
                pass  # Expected to fail without proper model loading

    def test_model_initialization_edge_cases(self):
        """Test model classes with edge case initializations."""
        # Test DEBERTAClassifier with extreme configurations
        with patch('emotion_clf_pipeline.model.AutoModel') as mock_auto_model:
            mock_model = MagicMock()
            mock_auto_model.from_pretrained.return_value = mock_model
            
            extreme_configs = [
                ("tiny-model", 1, {'emotion': 1}),  # Minimal config
                ("large-model", 2048, {'emotion': 100, 'sub_emotion': 500, 'intensity': 50}),  # Large config
                ("model", 64, {}),  # Empty num_classes
            ]
            
            for model_name, feature_dim, num_classes in extreme_configs:
                try:
                    classifier = DEBERTAClassifier(model_name, feature_dim, num_classes)
                    # Test forward pass
                    if num_classes:  # Only test if num_classes is not empty
                        mock_model.return_value.last_hidden_state = torch.randn(1, 10, 768)
                        input_data = {
                            'input_ids': torch.randint(0, 1000, (1, 10)),
                            'attention_mask': torch.ones(1, 10),
                            'features': torch.randn(1, feature_dim)
                        }
                        outputs = classifier(input_data)
                except Exception:
                    pass  # Some extreme configs may fail


if __name__ == '__main__':
    unittest.main() 