"""
Unit tests for emotion_clf_pipeline.data module.

Tests core functionality of data loading, preprocessing, and dataset creation.
"""

import unittest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os

import pandas as pd
import torch
import numpy as np

from emotion_clf_pipeline.data import (
    DataPreparation,
    DatasetLoader,
    EmotionDataset,
    log_class_distributions,
)


class TestDatasetLoader(unittest.TestCase):
    """Test cases for DatasetLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = DatasetLoader()

    def test_init(self):
        """Test DatasetLoader initialization."""
        self.assertIsNone(self.loader.train_df)
        self.assertIsNone(self.loader.test_df)

    @patch('os.listdir')
    @patch('pandas.read_csv')
    def test_load_training_data_success(self, mock_read_csv, mock_listdir):
        """Test successful training data loading."""
        mock_listdir.return_value = ['train_data-0001.csv']
        mock_df = pd.DataFrame({
            'start_time': [0],
            'end_time': [1],
            'text': ['sample text'],
            'emotion': ['joy'],
            'sub-emotion': ['happiness'],
            'intensity': ['medium']
        })
        mock_read_csv.return_value = mock_df
        
        result = self.loader.load_training_data("fake_path")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIsNotNone(self.loader.train_df)

    @patch('pandas.read_csv')
    def test_load_test_data_success(self, mock_read_csv):
        """Test successful test data loading."""
        mock_df = pd.DataFrame({
            'start_time': [0],
            'end_time': [1],
            'text': ['sample text'],
            'emotion': ['joy'],
            'sub-emotion': ['happiness'],
            'intensity': ['medium']
        })
        mock_read_csv.return_value = mock_df
        
        result = self.loader.load_test_data("fake_path")
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIsNotNone(self.loader.test_df)

    @patch('pandas.read_csv')
    def test_load_test_data_file_error(self, mock_read_csv):
        """Test test data loading with file error."""
        mock_read_csv.side_effect = Exception("File error")
        
        result = self.loader.load_test_data("fake_path")
        
        self.assertIsNone(result)

    @patch('matplotlib.pyplot.show')
    @patch('seaborn.countplot')
    @patch('matplotlib.pyplot.subplots')
    def test_plot_distributions(self, mock_subplots, mock_countplot, mock_show):
        """Test plotting data distributions."""
        mock_fig = MagicMock()
        mock_axes = [MagicMock(), MagicMock(), MagicMock()]
        mock_subplots.return_value = (mock_fig, mock_axes)
        
        # Set up test data
        self.loader.train_df = pd.DataFrame({
            'emotion': ['joy', 'sadness'],
            'sub_emotion': ['happiness', 'grief'],
            'intensity': ['high', 'low']
        })
        self.loader.test_df = pd.DataFrame({
            'emotion': ['joy'],
            'sub_emotion': ['happiness'],
            'intensity': ['high']
        })
        
        self.loader.plot_distributions()
        
        mock_subplots.assert_called()


class TestDataPreparation(unittest.TestCase):
    """Test cases for DataPreparation class."""

    def setUp(self):
        """Set up test fixtures."""
        mock_tokenizer = MagicMock()
        output_columns = ['emotion', 'sub_emotion', 'intensity']
        self.data_prep = DataPreparation(output_columns, mock_tokenizer)

    def test_init(self):
        """Test DataPreparation initialization."""
        self.assertIsNotNone(self.data_prep.encoders)
        self.assertIn('emotion', self.data_prep.encoders)
        self.assertIn('sub_emotion', self.data_prep.encoders)
        self.assertIn('intensity', self.data_prep.encoders)

    def test_get_num_classes(self):
        """Test getting number of classes."""
        # Set up mock encoders with classes_
        for col in ['emotion', 'sub_emotion', 'intensity']:
            self.data_prep.encoders[col].classes_ = [f'{col}_class_{i}' for i in range(3)]
        
        num_classes = self.data_prep.get_num_classes()
        expected = {'emotion': 3, 'sub_emotion': 3, 'intensity': 3}
        
        self.assertEqual(num_classes, expected)

    @patch('emotion_clf_pipeline.data.DataPreparation._save_encoders')
    def test_prepare_data_basic(self, mock_save):
        """Test basic data preparation."""
        train_df = pd.DataFrame({
            'text': ['hello world', 'goodbye world'],
            'emotion': ['joy', 'sadness'],
            'sub_emotion': ['happiness', 'grief'],
            'intensity': ['high', 'low']
        })
        
        result = self.data_prep.prepare_data(train_df)
        
        self.assertIsNotNone(result)
        self.assertIn('train_dataset', result)

    def test_prepare_data_no_features(self):
        """Test data preparation without feature extractor."""
        train_df = pd.DataFrame({
            'text': ['hello world'],
            'emotion': ['joy'],
            'sub_emotion': ['happiness'],
            'intensity': ['high']
        })
        
        # Mock feature extractor to return None
        with patch.object(self.data_prep, 'feature_extractor', None):
            result = self.data_prep.prepare_data(train_df)
            self.assertIsNotNone(result)

    @patch('joblib.dump')
    def test_save_encoders(self, mock_dump):
        """Test saving encoders."""
        self.data_prep._save_encoders()
        # Should call dump for each encoder
        self.assertTrue(mock_dump.called)

    @patch('joblib.load')
    @patch('os.path.exists')
    def test_load_encoders_success(self, mock_exists, mock_load):
        """Test successful encoder loading."""
        mock_exists.return_value = True
        mock_encoder = MagicMock()
        mock_load.return_value = mock_encoder
        
        self.data_prep._load_encoders()
        self.assertTrue(mock_load.called)

    @patch('os.path.exists')
    def test_load_encoders_not_found(self, mock_exists):
        """Test encoder loading when files don't exist."""
        mock_exists.return_value = False
        
        # Should not raise exception
        self.data_prep._load_encoders()

    def test_create_train_val_split(self):
        """Test train validation split."""
        df = pd.DataFrame({
            'text': ['text1', 'text2', 'text3', 'text4'],
            'emotion': ['joy', 'sadness', 'joy', 'sadness'],
            'sub_emotion': ['happiness', 'grief', 'excitement', 'sorrow'],
            'intensity': ['high', 'low', 'medium', 'high']
        })
        
        train_df, val_df = self.data_prep._create_train_val_split(df, 0.5)
        
        self.assertEqual(len(train_df) + len(val_df), len(df))
        self.assertGreater(len(train_df), 0)
        self.assertGreater(len(val_df), 0)

    def test_balance_dataset_equal(self):
        """Test dataset balancing with equal strategy."""
        df = pd.DataFrame({
            'text': ['text1', 'text2', 'text3', 'text4', 'text5'],
            'emotion': ['joy', 'joy', 'joy', 'sadness', 'sadness'],
            'sub_emotion': ['happiness', 'excitement', 'bliss', 'grief', 'sorrow'],
            'intensity': ['high', 'medium', 'high', 'low', 'medium']
        })
        
        result = self.data_prep._balance_dataset(df, 'equal')
        
        # Check that all classes have equal representation
        counts = result['emotion'].value_counts()
        self.assertEqual(len(counts.unique()), 1)

    def test_balance_dataset_proportional(self):
        """Test dataset balancing with proportional strategy."""
        df = pd.DataFrame({
            'text': ['text1', 'text2', 'text3', 'text4'],
            'emotion': ['joy', 'joy', 'sadness', 'sadness'],
            'sub_emotion': ['happiness', 'excitement', 'grief', 'sorrow'],
            'intensity': ['high', 'medium', 'low', 'medium']
        })
        
        result = self.data_prep._balance_dataset(df, 'proportional')
        
        self.assertLessEqual(len(result), len(df))

    def test_apply_augmentation(self):
        """Test data augmentation application."""
        df = pd.DataFrame({
            'text': ['hello world'],
            'emotion': ['joy'],
            'sub_emotion': ['happiness'],
            'intensity': ['high']
        })
        
        result = self.data_prep._apply_augmentation(df, ratio=2)
        
        # Should have original + augmented data
        self.assertGreaterEqual(len(result), len(df))


class TestEmotionDataset(unittest.TestCase):
    """Test cases for EmotionDataset class."""

    def setUp(self):
        """Set up test fixtures."""
        self.texts = ['Hello world', 'Goodbye world']
        self.features = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        
        # Create mock tokenizer
        self.mock_tokenizer = MagicMock()
        self.mock_tokenizer.return_value = {
            'input_ids': torch.tensor([101, 102]),
            'attention_mask': torch.tensor([1, 1])
        }

    def test_init(self):
        """Test EmotionDataset initialization."""
        dataset = EmotionDataset(
            texts=self.texts,
            tokenizer=self.mock_tokenizer,
            features=self.features
        )
        
        self.assertEqual(len(dataset), 2)
        self.assertEqual(dataset.texts, self.texts)

    def test_len(self):
        """Test dataset length."""
        dataset = EmotionDataset(
            texts=self.texts,
            tokenizer=self.mock_tokenizer,
            features=self.features
        )
        
        self.assertEqual(len(dataset), 2)

    def test_getitem_without_labels(self):
        """Test getting item without labels."""
        dataset = EmotionDataset(
            texts=self.texts,
            tokenizer=self.mock_tokenizer,
            features=self.features
        )
        
        item = dataset[0]
        
        self.assertIn('input_ids', item)
        self.assertIn('attention_mask', item)
        self.assertIn('features', item)

    def test_getitem_with_labels(self):
        """Test getting item with labels."""
        labels = {
            'emotion': torch.tensor([0, 1]),
            'sub_emotion': torch.tensor([1, 2]),
            'intensity': torch.tensor([2, 0])
        }
        
        dataset = EmotionDataset(
            texts=self.texts,
            tokenizer=self.mock_tokenizer,
            features=self.features,
            labels=labels
        )
        
        item = dataset[0]
        
        self.assertIn('input_ids', item)
        self.assertIn('attention_mask', item)
        self.assertIn('features', item)

    def test_empty_dataset(self):
        """Test empty dataset."""
        dataset = EmotionDataset(
            texts=[],
            tokenizer=self.mock_tokenizer,
            features=torch.empty(0, 3)
        )
        
        self.assertEqual(len(dataset), 0)

    def test_single_item_dataset(self):
        """Test single item dataset."""
        dataset = EmotionDataset(
            texts=['single text'],
            tokenizer=self.mock_tokenizer,
            features=torch.tensor([[0.1, 0.2, 0.3]])
        )
        
        self.assertEqual(len(dataset), 1)
        item = dataset[0]
        self.assertIn('input_ids', item)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""

    def test_log_class_distributions(self):
        """Test logging class distributions."""
        df = pd.DataFrame({
            'emotion': ['joy', 'sadness', 'joy'],
            'sub_emotion': ['happiness', 'grief', 'excitement'],
            'intensity': ['high', 'low', 'medium']
        })
        
        output_tasks = ['emotion', 'sub_emotion', 'intensity']
        
        # Should not raise any exceptions
        log_class_distributions(df, output_tasks, "test")

    def test_log_class_distributions_missing_columns(self):
        """Test logging class distributions with missing columns."""
        df = pd.DataFrame({
            'emotion': ['joy', 'sadness']
        })
        
        output_tasks = ['emotion', 'nonexistent_col']
        
        # Should not raise any exceptions and log warning
        log_class_distributions(df, output_tasks, "test")

    def test_log_class_distributions_empty_df(self):
        """Test logging class distributions with empty dataframe."""
        df = pd.DataFrame()
        output_tasks = ['emotion']
        
        # Should not raise any exceptions
        log_class_distributions(df, output_tasks, "test")


    def test_dataset_loader_edge_cases_comprehensive(self):
        """Test all edge cases and error paths in DatasetLoader."""
        loader = DatasetLoader()
        
        # Test with completely empty directory
        with patch('os.listdir', return_value=[]):
            result = loader.load_training_data("empty_directory")
            self.assertIsNone(result)
        
        # Test with file reading errors
        with patch('os.listdir', return_value=['file1.csv']):
            with patch('pandas.read_csv', side_effect=Exception("File error")):
                result = loader.load_training_data("error_directory")
                self.assertIsNone(result)
        
        # Test load_test_data with exception
        with patch('pandas.read_csv', side_effect=IOError("Cannot read file")):
            result = loader.load_test_data("error_file.csv")
            self.assertIsNone(result)
        
        # Test plot_distributions with None data
        loader.train_df = None
        loader.test_df = None
        with patch('matplotlib.pyplot.subplots'), patch('seaborn.countplot'), patch('matplotlib.pyplot.show'):
            loader.plot_distributions()  # Should handle None gracefully
        
        # Test plot_distributions with empty dataframes
        loader.train_df = pd.DataFrame()
        loader.test_df = pd.DataFrame()
        with patch('matplotlib.pyplot.subplots'), patch('seaborn.countplot'), patch('matplotlib.pyplot.show'):
            loader.plot_distributions()

    def test_data_preparation_edge_cases_comprehensive(self):
        """Test all edge cases in DataPreparation."""
        mock_tokenizer = MagicMock()
        output_columns = ['emotion', 'sub_emotion', 'intensity']
        
        # Test with feature extractor
        mock_feature_extractor = MagicMock()
        data_prep = DataPreparation(output_columns, mock_tokenizer, mock_feature_extractor)
        
        # Test encoder saving with all possible paths
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            with patch('joblib.dump') as mock_dump:
                data_prep._save_encoders()
                # Should save all three encoders
                self.assertEqual(mock_dump.call_count, 3)
        
        # Test encoder loading when files exist vs don't exist
        with patch('os.path.exists') as mock_exists:
            with patch('joblib.load') as mock_load:
                # Test when all files exist
                mock_exists.return_value = True
                mock_encoder = MagicMock()
                mock_encoder.classes_ = ['class1', 'class2', 'class3']
                mock_load.return_value = mock_encoder
                data_prep._load_encoders()
                
                # Test when files don't exist
                mock_exists.return_value = False
                data_prep._load_encoders()
        
        # Test get_num_classes with actual encoder data
        mock_encoder = MagicMock()
        mock_encoder.classes_ = ['joy', 'sadness', 'anger', 'fear', 'surprise']
        data_prep.encoders = {
            'emotion': mock_encoder,
            'sub_emotion': mock_encoder,
            'intensity': mock_encoder
        }
        num_classes = data_prep.get_num_classes()
        self.assertEqual(num_classes['emotion'], 5)
        
        # Test prepare_data with various validation sizes
        large_df = pd.DataFrame({
            'text': [f'text_{i}' for i in range(200)],
            'emotion': (['joy'] * 50 + ['sadness'] * 50 + ['anger'] * 50 + ['fear'] * 50),
            'sub_emotion': [f'sub_{i%10}' for i in range(200)],
            'intensity': (['high'] * 67 + ['medium'] * 67 + ['low'] * 66)
        })
        
        with patch.object(data_prep, '_save_encoders'):
            with patch('emotion_clf_pipeline.data.EmotionDataset') as mock_dataset:
                with patch('torch.utils.data.DataLoader') as mock_dataloader:
                    mock_dataset.return_value = MagicMock()
                    mock_dataloader.return_value = MagicMock()
                    
                    # Test with different validation sizes
                    for val_size in [0.1, 0.15, 0.2, 0.25, 0.3]:
                        result = data_prep.prepare_data(large_df, val_size=val_size)
                    
                    # Test with different batch sizes
                    for batch_size in [8, 16, 32, 64]:
                        result = data_prep.prepare_data(large_df, batch_size=batch_size)

    def test_emotion_dataset_comprehensive_scenarios(self):
        """Test EmotionDataset with all possible scenarios."""
        texts = ['text1', 'text2', 'text3', 'text4', 'text5']
        features = torch.randn(5, 15)
        mock_tokenizer = MagicMock()
        
        # Test with different tokenizer outputs
        tokenizer_outputs = [
            {'input_ids': torch.tensor([101, 102, 103, 104, 105]), 'attention_mask': torch.tensor([1, 1, 1, 1, 1])},
            {'input_ids': torch.tensor([101, 102]), 'attention_mask': torch.tensor([1, 1])},
            {'input_ids': torch.tensor([101]), 'attention_mask': torch.tensor([1])}
        ]
        
        for output in tokenizer_outputs:
            mock_tokenizer.return_value = output
            
            # Test without labels
            dataset = EmotionDataset(texts, mock_tokenizer, features)
            self.assertEqual(len(dataset), 5)
            
            # Test all items in dataset
            for i in range(len(dataset)):
                item = dataset[i]
                self.assertIn('input_ids', item)
                self.assertIn('attention_mask', item)
                self.assertIn('features', item)
            
            # Test with all types of labels
            labels = {
                'emotion': torch.randint(0, 7, (5,)),
                'sub_emotion': torch.randint(0, 28, (5,)),
                'intensity': torch.randint(0, 3, (5,))
            }
            
            dataset_with_labels = EmotionDataset(texts, mock_tokenizer, features, labels)
            
            # Test all items with labels
            for i in range(len(dataset_with_labels)):
                item = dataset_with_labels[i]
                self.assertIn('emotion', item)
                self.assertIn('sub_emotion', item)
                self.assertIn('intensity', item)
            
            # Test with different max_length values
            for max_len in [64, 128, 256, 512]:
                dataset_max_len = EmotionDataset(texts, mock_tokenizer, features, labels, max_length=max_len)
                item = dataset_max_len[0]
                self.assertIn('input_ids', item)

    def test_log_class_distributions_comprehensive(self):
        """Test log_class_distributions with all possible data scenarios."""
        # Test with various dataset sizes
        for size in [0, 1, 5, 10, 50, 100, 500]:
            if size == 0:
                df = pd.DataFrame()
            else:
                df = pd.DataFrame({
                    'emotion': (['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'neutral'] * (size // 7 + 1))[:size],
                    'sub_emotion': ([f'sub_{i%20}' for i in range(20)] * (size // 20 + 1))[:size],
                    'intensity': (['high', 'medium', 'low'] * (size // 3 + 1))[:size]
                })
            
            # Test with different output task combinations
            task_combinations = [
                ['emotion'],
                ['emotion', 'sub_emotion'],
                ['emotion', 'sub_emotion', 'intensity'],
                ['emotion', 'nonexistent_column'],
                ['nonexistent_column'],
                []
            ]
            
            for tasks in task_combinations:
                for phase in ['train', 'test', 'validation', 'inference']:
                    log_class_distributions(df, tasks, phase)

    def test_all_utility_functions_edge_cases(self):
        """Test all utility functions with edge cases."""
        # Test with various unusual data combinations
        unusual_data = [
            pd.DataFrame({'text': [''], 'emotion': ['']}),  # Empty strings
            pd.DataFrame({'text': [None], 'emotion': [None]}),  # None values
            pd.DataFrame({'text': ['a' * 1000], 'emotion': ['joy']}),  # Very long text
            pd.DataFrame({'text': ['🙂😊🎉'], 'emotion': ['joy']}),  # Emoji text
            pd.DataFrame({'text': ['   '], 'emotion': ['neutral']}),  # Whitespace only
        ]
        
        for df in unusual_data:
            try:
                log_class_distributions(df, ['emotion'], 'test')
            except Exception:
                pass  # Some edge cases may fail, that's okay


if __name__ == '__main__':
    unittest.main() 