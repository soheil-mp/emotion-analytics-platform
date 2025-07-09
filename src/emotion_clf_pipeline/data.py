from __future__ import annotations

import argparse
import json
import logging
import os
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoTokenizer

# Import FeatureExtractor from .features
try:
    from .azure_pipeline import register_processed_data_assets_from_paths
    from .features import FeatureExtractor
except ImportError:
    from azure_pipeline import register_processed_data_assets_from_paths
    from features import FeatureExtractor

logger = logging.getLogger(__name__)


def log_class_distributions(df: pd.DataFrame, output_tasks: list[str], df_name: str):
    """Logs the class distribution for specified tasks in a dataframe."""
    logger.info(f"{df_name.capitalize()} data class distributions:")
    logger.info(f"Available {df_name} columns: {list(df.columns)}")
    for col in output_tasks:
        if col in df.columns:
            dist = df[col].value_counts(normalize=True).to_dict()
            logger.info(f"  {col}: {json.dumps(dist, indent=2)}")
        else:
            logger.warning(f"  {col}: COLUMN NOT FOUND in {df_name} data")


class DatasetLoader:
    """
    A class to handle loading and preprocessing of emotion classification datasets.

    This class handles:
    - Loading training and test data from CSV files
    - Cleaning and preprocessing the data
    - Mapping emotions to standardized categories
    - Visualizing data distributions

    Attributes:
        emotion_mapping (dict): Dictionary mapping sub-emotions to standardized emotions
        train_df (pd.DataFrame): Processed training data
        test_df (pd.DataFrame): Processed test data
    """

    def __init__(self):

        # Initialize the DataLoader with emotion mapping.
        self.train_df = None
        self.test_df = None

    def load_training_data(self, data_dir="./../../data/raw/all groups"):
        """
        Load and preprocess training data from multiple CSV files.

        Args:
            data_dir (str): Directory containing training data CSV files

        Returns:
            pd.DataFrame: Processed training data
        """

        # Load the dataset (contains train_data-0001.csv, train_data-0002.csv, etc.)
        self.train_df = pd.DataFrame()

        # Loop over all files in the data directory
        for i_file in os.listdir(data_dir):

            # If the file is not a CSV, skip it
            if not i_file.endswith(".csv"):
                logger.warning(f"Skipping non-CSV file: {i_file}")
                continue

            # Read the current CSV file and select specific columns
            try:
                df_ = pd.read_csv(os.path.join(data_dir, i_file))[
                    [
                        "start_time",
                        "end_time",
                        "text",
                        "emotion",
                        "sub-emotion",
                        "intensity",
                    ]
                ]
            except Exception as e:
                logger.error(f"Error reading {i_file}: {e}")
                continue

            # Handle column name variations (sub-emotion vs sub_emotion)
            if "sub-emotion" in df_.columns:
                df_ = df_.rename(columns={"sub-emotion": "sub_emotion"})

            # Concatenate the current file's data with the main DataFrame
            self.train_df = pd.concat([self.train_df, df_])

        # Drop null and duplicate rows
        self.train_df = self.train_df.dropna()
        self.train_df = self.train_df.drop_duplicates()

        # Reset index of the combined DataFrame
        self.train_df = self.train_df.reset_index(drop=True)

        return self.train_df

    def load_test_data(self, test_file="./../../data/test_data-0001.csv"):
        """
        Load and preprocess test data from a CSV file.

        Args:
            test_file (str): Path to the test data CSV file

        Returns:
            pd.DataFrame: Processed test data
        """

        # Read the test data CSV file
        try:
            self.test_df = pd.read_csv(test_file)[
                [
                    "start_time",
                    "end_time",
                    "text",
                    "emotion",
                    "sub-emotion",
                    "intensity",
                ]
            ]
        except Exception as e:
            logger.error(f"Error reading test file {test_file}: {e}")
            return None

        # Handle column name variations (sub-emotion vs sub_emotion)
        if "sub-emotion" in self.test_df.columns:
            self.test_df = self.test_df.rename(columns={"sub-emotion": "sub_emotion"})

        # Drop null and duplicate rows
        self.test_df = self.test_df.dropna()
        self.test_df = self.test_df.drop_duplicates()

        # Reset index of the test DataFrame
        self.test_df = self.test_df.reset_index(drop=True)

        return self.test_df

    def plot_distributions(self):
        """Plot distributions of emotions, sub-emotions, and intensities \
            for both training and test sets."""
        # Distribution of emotions in the training set
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        for i, col in enumerate(["emotion", "sub_emotion", "intensity"]):
            sns.countplot(data=self.train_df, x=col, palette="Set2", ax=axes[i])
            axes[i].set_title(f"'{col.capitalize()}' Distribution in Train/Val Set")
            axes[i].set_xlabel(col.capitalize())
            axes[i].set_ylabel("Count")
            axes[i].tick_params(axis="x", rotation=45)
        plt.tight_layout()
        plt.show()

        # Distribution of emotions in the test set
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        for i, col in enumerate(["emotion", "sub_emotion", "intensity"]):
            sns.countplot(data=self.test_df, x=col, palette="Set2", ax=axes[i])
            axes[i].set_title(f"'{col.capitalize()}' Distribution in Test Set")
            axes[i].set_xlabel(col.capitalize())
            axes[i].set_ylabel("Count")
            axes[i].tick_params(axis="x", rotation=45)
        plt.tight_layout()
        plt.show()


class DataPreparation:
    """
    A class to handle data preparation for emotion classification tasks.

    This class handles:
    - Label encoding for target variables
    - Dataset creation
    - Dataloader setup

    Args:
        output_columns (list): List of output column names to encode
        model_name (str): Name of the pretrained model to use for tokenization
        max_length (int): Maximum sequence length for tokenization
        batch_size (int): Batch size for dataloaders
        feature_config (dict, optional): Configuration for feature extraction
    """

    def __init__(
        self,
        output_columns,
        tokenizer,
        max_length=128,
        batch_size=16,
        feature_config=None,
        encoders_save_dir=None,
        encoders_load_dir=None,
    ):
        self.output_columns = output_columns
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.batch_size = batch_size

        # Initialize label encoders
        self.label_encoders = {col: LabelEncoder() for col in output_columns}

        # Determine project root directory to construct lexicon path
        _current_file_path_dp = os.path.abspath(__file__)
        # Assuming data.py is in src/emotion_clf_pipeline/
        _project_root_dir_dp = os.path.dirname(
            os.path.dirname(os.path.dirname(_current_file_path_dp))
        )

        # Fix for Docker container: if we're in /app, use /app as project root
        if _project_root_dir_dp == "/" and os.path.exists("/app/models"):
            _project_root_dir_dp = "/app"

        emolex_lexicon_path = os.path.join(
            _project_root_dir_dp,
            "models",
            "features",
            "EmoLex",
            "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
        )
        # Use provided encoders_save_dir or default
        self.encoders_output_dir = (
            encoders_save_dir
            if encoders_save_dir
            else os.path.join(_project_root_dir_dp, "models", "encoders")
        )

        # Store encoders_load_dir
        self.encoders_input_dir = encoders_load_dir

        # Attempt to load encoders if encoders_input_dir is provided
        self.encoders_loaded = self._load_encoders()

        # Initialize feature extractor with configuration and lexicon path
        self.feature_extractor = FeatureExtractor(
            feature_config=feature_config, lexicon_path=emolex_lexicon_path
        )

    def _load_encoders(self):
        """Load label encoders from disk if encoders_input_dir is set."""
        if not self.encoders_input_dir:
            logger.info(
                "Encoder input directory not provided."
                " Will fit new encoders if training."
            )
            return False

        loaded_all = True
        for col in self.output_columns:
            encoder_path = os.path.join(self.encoders_input_dir, f"{col}_encoder.pkl")
            if os.path.exists(encoder_path):
                try:
                    with open(encoder_path, "rb") as f:
                        # Load trusted sklearn encoder from controlled environment
                        self.label_encoders[col] = pickle.load(f)  # nosec B301
                    logger.info(f"Loaded encoder for {col} from {encoder_path}")
                except Exception as e:
                    logger.error(
                        f"Error loading encoder for {col} from {encoder_path}: {e}."
                        " A new encoder will be used."
                    )
                    self.label_encoders[col] = LabelEncoder()
                    loaded_all = False
            else:
                logger.warning(
                    f"Encoder file not found for {col} at {encoder_path}. "
                    "A new encoder will be used and fitted if train data is provided."
                )
                self.label_encoders[col] = LabelEncoder()
                loaded_all = False

        if loaded_all:
            logger.info("All encoders loaded successfully.")
        else:
            logger.warning(
                "One or more encoders failed to load or were not found. "
                "New encoders will be fitted for these if training data is provided."
            )
        return loaded_all

    # def apply_data_augmentation(
    #     self,
    #     train_df,
    #     balance_strategy="equal",
    #     samples_per_class=None,
    #     augmentation_ratio=2,
    #     random_state=42,
    # ):
    #     """
    #     Apply text augmentation to balance the training data.

    #     Args:
    #         train_df (pd.DataFrame): Training dataframe
    #         balance_strategy (str, optional): Strategy for balancing. Options:
    #         'equal', 'majority', 'target'. Defaults to 'equal'.
    #         samples_per_class (int, optional): Number of samples per class for
    #         'equal' or 'target' strategy. Defaults to None.
    #         augmentation_ratio (int, optional): Maximum ratio of augmented to
    #         original samples. Defaults to 2.
    #         random_state (int, optional): Random seed. Defaults to 42.

    #     Returns:
    #         pd.DataFrame: Balanced training dataframe
    #     """
    #     logger.info(f"Applying data augmentation with strategy: {balance_strategy}")
    #     original_class_dist = train_df["emotion"].value_counts()
    #     logger.info("Original class distribution:")
    #     for emotion, count in original_class_dist.items():
    #         logger.info(f"  {emotion}: {count}")

    #     # Create an instance of TextAugmentor
    #     augmentor = TextAugmentor(random_state=random_state)

    #     # Apply the appropriate balancing strategy
    #     if balance_strategy == "equal":
    #         # Generate exactly equal samples per class
    #         if samples_per_class is None:
    #             # If not specified, use the average count
    #             samples_per_class = int(
    #                 len(train_df) / len(train_df["emotion"].unique())
    #             )

    #         balanced_df = augmentor.generate_equal_samples(
    #             train_df,
    #             text_column="text",
    #             emotion_column="emotion",
    #             samples_per_class=samples_per_class,
    #             random_state=random_state,
    #         )

    #     elif balance_strategy == "majority":
    #         # Balance up to the majority class
    #         balanced_df = augmentor.balance_dataset(
    #             train_df,
    #             text_column="text",
    #             emotion_column="emotion",
    #             target_count=None,  # Use majority class count
    #             augmentation_ratio=augmentation_ratio,
    #             random_state=random_state,
    #         )

    #     elif balance_strategy == "target":
    #         # Balance to a target count
    #         if samples_per_class is None:
    #             # If not specified, use the median count
    #             samples_per_class = int(train_df["emotion"].value_counts().median())

    #         balanced_df = augmentor.balance_dataset(
    #             train_df,
    #             text_column="text",
    #             emotion_column="emotion",
    #             target_count=samples_per_class,
    #             augmentation_ratio=augmentation_ratio,
    #             random_state=random_state,
    #         )

    #     else:
    #         raise ValueError(f"Unknown balance strategy: {balance_strategy}")

    #     # Apply additional sub-emotion balancing if needed
    #     if "sub_emotion" in self.output_columns:
    #         logger.info("After emotion balancing, checking sub-emotion distribution:")
    #         sub_emotion_dist = balanced_df["sub_emotion"].value_counts()
    #         logger.info(f"Sub-emotion classes: {len(sub_emotion_dist)}")
    #         logger.info(
    #             f"Min class size: {sub_emotion_dist.min()}, "
    #             f"Max class size: {sub_emotion_dist.max()}"
    #         )

    #         # If sub-emotion is highly imbalanced, apply additional balancing
    #         imbalance_ratio = sub_emotion_dist.max() / sub_emotion_dist.min()
    #         if imbalance_ratio > 5:  # If max/min ratio is greater than 5
    #             logger.info(
    #                 f"Sub-emotion imbalance ratio: {imbalance_ratio:.1f}, "
    #                 "applying additional balancing"
    #             )

    #             # Apply augmentation for sub-emotions with extreme imbalance
    #             sub_balanced_df = augmentor.balance_dataset(
    #                 balanced_df,
    #                 text_column="text",
    #                 emotion_column="sub_emotion",
    #                 target_count=max(
    #                     50, sub_emotion_dist.median() // 2
    #                 ),  # Target at least 50 samples or half median
    #                 augmentation_ratio=1,  # Keep augmentation minimal
    #                 random_state=random_state,
    #             )
    #             balanced_df = sub_balanced_df

    #     return balanced_df

    def prepare_data(
        self,
        train_df,
        test_df=None,
        validation_split=0.2,
        apply_augmentation=False,
        balance_strategy="equal",
        samples_per_class=None,
        augmentation_ratio=2,
    ):
        """
        Prepare data for training emotion classification models.

        Args:
            train_df (pd.DataFrame): Training dataframe
            test_df (pd.DataFrame, optional): Test dataframe. Defaults to None.
            validation_split (float, optional): Fraction of training data to use
            for validation. Defaults to 0.2.
            apply_augmentation (bool, optional): Whether to apply data
            augmentation. Defaults to False.
            balance_strategy (str, optional): Strategy for balancing if
            augmentation is applied. Options: 'equal', 'majority', 'target'.
            Defaults to 'equal'.
            samples_per_class (int, optional): Number of samples per class for
            balancing. Defaults to None.
            augmentation_ratio (int, optional): Maximum ratio of augmented to
            original samples. Defaults to 2.

        Returns:
            tuple: (train_dataset, val_dataset, test_dataset, train_dataloader,
            val_dataloader, test_dataloader, class_weights_tensor)
        """
        # Handle evaluation-only scenario (train_df is None)
        is_evaluation_only = train_df is None
        if is_evaluation_only:
            logger.info(
                "Evaluation-only mode: train_df is None, "
                "skipping training data preparation"
            )

            # Ensure encoders are loaded for evaluation
            if not self.encoders_loaded:
                logger.error(
                    "Cannot perform evaluation without pre-loaded encoders "
                    "when train_df is None"
                )
                raise ValueError(
                    "Label encoders must be pre-loaded for evaluation-only mode"
                )

            logger.info("Using pre-loaded label encoders for evaluation")
        else:
            # Standard training/validation preparation
            # Create output directory for encoders if needed
            if not self.encoders_loaded and self.encoders_output_dir:
                os.makedirs(self.encoders_output_dir, exist_ok=True)
                logger.info(
                    f"Ensured encoder output dir exists: {self.encoders_output_dir}"
                )

            # Fit label encoders on training data ONLY IF NOT LOADED
            if not self.encoders_loaded:
                logger.info(
                    "Fitting new label encoders as they were not loaded or load failed."
                )
                for col in self.output_columns:
                    if col in train_df.columns:
                        # Ensure the column is treated as string for consistent fitting
                        self.label_encoders[col].fit(train_df[col].astype(str))
                        logger.info(f"Fitted encoder for column: {col}")
                    else:
                        logger.warning(
                            f"Column {col} not found in train_df for fitting encoder."
                        )
                # Save label encoders if they were just fitted
                # and a save directory is provided
                if self.encoders_output_dir:
                    self._save_encoders()
            else:
                logger.info("Using pre-loaded label encoders.")

            # Transform training data labels
            for col in self.output_columns:
                if col in train_df.columns:
                    try:
                        # Ensure the column is treated as string for
                        # consistent transformation
                        train_df[f"{col}_encoded"] = self.label_encoders[col].transform(
                            train_df[col].astype(str)
                        )
                    except ValueError as e:
                        logger.error(
                            f"Error transforming column {col} in training data: {e}"
                        )
                        logger.error(
                            f"Classes known to encoder for {col}: "
                            " {list(self.label_encoders[col].classes_) if "
                            " hasattr(self.label_encoders[col], 'classes_') else "
                            " 'Encoder not fitted or classes_ not available'}"
                        )
                        raise e
                else:
                    logger.warning(
                        f"Column {col} (for encoding) not found in train_df."
                    )

        # Handle training data preparation (skip if evaluation-only)
        train_dataset = None
        val_dataset = None
        train_dataloader = None
        val_dataloader = None

        if not is_evaluation_only:
            # Split into train and validation sets
            if validation_split == 0.0:
                train_indices = list(range(len(train_df)))
                val_indices = []
                logger.info(
                    "validation_split is 0.0, using all train_df for train_indices."
                )
            elif validation_split > 0 and validation_split < 1:
                stratify_on = None
                if self.output_columns and self.output_columns[0] in train_df:
                    # sklearn's train_test_split handles cases with single class
                    # for stratification
                    # by not stratifying if it's not possible.
                    stratify_on = train_df[self.output_columns[0]]

                train_indices, val_indices = train_test_split(
                    range(len(train_df)),
                    test_size=validation_split,
                    random_state=42,
                    stratify=stratify_on,
                )
            else:
                # If validation_split is not 0.0 and not in (0.0, 1.0)
                # This case should ideally not be hit with current CLI usage
                # (0.0 or 0.1).
                raise ValueError(
                    f"Unsupported validation_split value: {validation_split}. "
                    " Must be 0.0 or in (0.0, 1.0)."
                )

            # Fit TF-IDF vectorizer on training texts
            logger.info("Fitting TF-IDF vectorizer...")
            self.feature_extractor.fit_tfidf(train_df["text"].values)

            # Extract features for all texts
            logger.info("Extracting features for training data...")
            train_features = []
            for text in tqdm(
                train_df["text"],
                desc="Processing training texts",
                ncols=120,
                colour="green",
            ):
                train_features.append(self.feature_extractor.extract_all_features(text))
            train_features = np.array(train_features)

            # Create train and validation datasets
            train_dataset = EmotionDataset(
                texts=train_df["text"].values[train_indices],
                labels=train_df[
                    [f"{col}_encoded" for col in self.output_columns]
                ].values[train_indices],
                features=train_features[train_indices],
                tokenizer=self.tokenizer,
                max_length=self.max_length,
                output_tasks=self.output_columns,
            )

            val_dataset = None
            if val_indices:
                val_dataset = EmotionDataset(
                    texts=train_df["text"].values[val_indices],
                    labels=train_df[
                        [f"{col}_encoded" for col in self.output_columns]
                    ].values[val_indices],
                    features=train_features[val_indices],
                    tokenizer=self.tokenizer,
                    max_length=self.max_length,
                    output_tasks=self.output_columns,
                )

            # Create dataloaders
            train_dataloader = DataLoader(
                train_dataset, batch_size=self.batch_size, shuffle=True
            )
            val_dataloader = (
                DataLoader(val_dataset, batch_size=self.batch_size, shuffle=False)
                if val_dataset
                else None
            )

        # Create test dataloader if test data is provided
        test_dataloader = None
        if test_df is not None:
            # For evaluation-only mode, ensure feature extractor is fitted
            if is_evaluation_only:
                logger.info(
                    "Evaluation-only mode: Assuming feature extractor is pre-fitted"
                )
                # If not fitted, this will raise an error which is expected behavior

            # Transform test data labels
            for col in self.output_columns:
                if col in test_df.columns:
                    # Ensure consistency with fitting: apply .astype(str)
                    test_df[f"{col}_encoded"] = self.label_encoders[col].transform(
                        test_df[col].astype(str)
                    )

            # Extract features for test texts
            logger.info("Extracting features for test data...")
            test_features = []
            for text in tqdm(
                test_df["text"],
                desc="Processing test texts",
                ncols=120,
                colour="blue",
            ):
                test_features.append(self.feature_extractor.extract_all_features(text))
            test_features = np.array(test_features)

            # Transform test labels
            for col in self.output_columns:
                if col in test_df.columns:
                    try:
                        # Ensure the column is treated as string for consistent
                        # transformation
                        test_df[f"{col}_encoded"] = self.label_encoders[col].transform(
                            test_df[col].astype(str)
                        )
                    except ValueError as e:
                        logger.error(
                            f"Error transforming column {col} in test data: {e}"
                        )
                        raise e
                else:
                    logger.warning(f"Column {col} (for encoding) not found in test_df.")

            # Get labels
            if all(f"{col}_encoded" in test_df.columns for col in self.output_columns):
                # If all output columns have encoded labels, use them
                test_labels = test_df[
                    [f"{col}_encoded" for col in self.output_columns]
                ].values
            else:
                # If not all output columns have encoded labels, set to None
                test_labels = None

            test_dataset = EmotionDataset(
                texts=test_df["text"].values,
                labels=test_labels,
                features=test_features,
                tokenizer=self.tokenizer,
                feature_extractor=self.feature_extractor,
                max_length=self.max_length,
                output_tasks=self.output_columns,
            )
            test_dataloader = DataLoader(test_dataset, batch_size=self.batch_size)

        # Make a copy of the dataframes to avoid modifying the originals
        # Store processed dataframes as attributes
        if train_df is not None:
            self.train_df_processed = train_df.copy()
        else:
            self.train_df_processed = None

        if test_df is not None:
            self.test_df_processed = test_df.copy()
            self.test_df_split = test_df.copy()
        else:
            self.test_df_processed = None
            self.test_df_split = None

        # Apply data augmentation if requested
        if apply_augmentation:
            # Assuming augmentation logic might be added here or called
            # For now, if it was empty, it remains effectively so.
            # If self.apply_data_augmentation was intended:
            # train_df = self.apply_data_augmentation(train_df, balance_strategy,
            #  samples_per_class, augmentation_ratio)
            # And then train_dataset/val_dataset would need to be recreated or updated.
            # This is a potential latent issue if augmentation is used.
            pass

        return train_dataloader, val_dataloader, test_dataloader

    def _save_encoders(self):
        """Save label encoders to disk."""
        if not self.encoders_output_dir:
            logger.warning(
                "Encoders output directory not set. Skipping saving encoders."
            )
            return
        os.makedirs(self.encoders_output_dir, exist_ok=True)
        for col, encoder in self.label_encoders.items():
            encoder_path = os.path.join(self.encoders_output_dir, f"{col}_encoder.pkl")
            with open(encoder_path, "wb") as f:
                pickle.dump(encoder, f)

    def get_num_classes(self):
        """Get the number of classes for each output column."""
        num_classes = {}
        for col in self.output_columns:
            if hasattr(self.label_encoders[col], "classes_"):
                num_classes[col] = len(self.label_encoders[col].classes_)
            else:
                # This case should ideally not happen if encoders are always
                # fitted or loaded before this call
                # logger.warning(f"Label encoder for column {col} does not have "
                #     "classes_ attribute. It might not have been fitted or "
                #     "loaded correctly."
                # )
                num_classes[col] = 0
        return num_classes


class EmotionDataset(Dataset):
    """Custom Dataset for emotion classification."""

    def __init__(
        self,
        texts,
        tokenizer,
        features,
        labels=None,
        feature_extractor=None,
        max_length=128,
        output_tasks=None,
    ):
        """
        Initialize the dataset.

        Args:
            texts (list): List of text samples
            tokenizer: BERT tokenizer
            features (np.ndarray): Pre-extracted features
            labels (list, optional): List of label tuples (emotion, sub_emotion,
            intensity). None for prediction.
            feature_extractor (FeatureExtractor, optional): Feature extractor
            instance. Not strictly needed if features are pre-computed.
            max_length (int): Maximum sequence length for BERT
            output_tasks (list, optional): List of tasks to output. Used only if
            labels are provided.
        """
        self.texts = texts
        self.tokenizer = tokenizer
        self.features = features  # Should be pre-calculated and correctly dimensioned
        self.labels = labels
        # self.feature_extractor = feature_extractor
        self.max_length = max_length
        self.output_tasks = output_tasks

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        item = {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "features": torch.tensor(self.features[idx], dtype=torch.float32),
        }

        # Add labels if they are available (i.e., during training/evaluation)
        if self.labels is not None and self.output_tasks is not None:
            current_labels = self.labels[idx]
            for i, task in enumerate(self.output_tasks):
                item[f"{task}_label"] = torch.tensor(
                    current_labels[i], dtype=torch.long
                )

        return item


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Data processing and feature engineering pipeline"
    )
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
        help="Register the processed data as assets in Azure ML",
    )

    args = parser.parse_args()
    return args


def main():
    """Main function to run the data processing pipeline."""
    load_dotenv()
    args = parse_args()

    # Setup logging
    log_file = os.path.join(args.output_dir, "data_processing.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        filename=log_file,
    )
    logger.info("=== Starting Data Processing Pipeline ===")

    # Parse output tasks
    output_tasks = [task.strip() for task in args.output_tasks.split(",")]

    # Update output_tasks to use underscore instead of hyphen
    # for consistency with data columns
    output_tasks = [task.replace("sub-emotion", "sub_emotion") for task in output_tasks]

    # Set paths from arguments
    RAW_TRAIN_PATH = args.raw_train_path
    RAW_TEST_FILE = args.raw_test_path
    PROCESSED_DATA_DIR = args.output_dir
    ENCODERS_DIR = args.encoders_dir

    # Processing parameters
    MODEL_NAME = args.model_name_tokenizer
    MAX_LENGTH = args.max_length
    BATCH_SIZE = 16

    # Feature configuration
    FEATURE_CONFIG = {
        "pos": False,
        "textblob": False,
        "vader": False,
        "tfidf": True,
        "emolex": True,
    }

    # Intensity mapping for standardization
    INTENSITY_MAPPING = {
        "mild": "mild",
        "neutral": "mild",
        "moderate": "moderate",
        "intense": "strong",
        "overwhelming": "strong",
    }

    # Create output directories
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(ENCODERS_DIR, exist_ok=True)

    try:
        # ====================================================================
        # STEP 1: Load Raw Data
        # ====================================================================
        logger.info("Step 1: Loading raw data...")

        dataset_loader = DatasetLoader()

        # Load training data
        if os.path.isdir(RAW_TRAIN_PATH):
            logger.info(f"Loading training data from directory: {RAW_TRAIN_PATH}")
            train_df = dataset_loader.load_training_data(data_dir=RAW_TRAIN_PATH)
        elif os.path.isfile(RAW_TRAIN_PATH):
            logger.info(f"Loading training data from file: {RAW_TRAIN_PATH}")
            train_df = pd.read_csv(RAW_TRAIN_PATH)
        else:
            logger.error(f"Training data path not found: {RAW_TRAIN_PATH}")
            raise FileNotFoundError(f"Training data path not found: {RAW_TRAIN_PATH}")

        # Load test data
        if os.path.exists(RAW_TEST_FILE):
            if os.path.isdir(RAW_TEST_FILE):
                logger.info(f"Loading test data from directory: {RAW_TEST_FILE}")
                # If test data is a directory, load all CSV files in it
                test_files = []
                for file in os.listdir(RAW_TEST_FILE):
                    if file.endswith(".csv"):
                        test_files.append(os.path.join(RAW_TEST_FILE, file))

                if test_files:
                    # Load and combine all test CSV files
                    test_dfs = []
                    for test_file in test_files:
                        logger.info(f"Loading test file: {test_file}")
                        df = dataset_loader.load_test_data(test_file=test_file)
                        if df is not None:
                            test_dfs.append(df)

                    if test_dfs:
                        test_df = pd.concat(test_dfs, ignore_index=True)
                        logger.info(f"Combined {len(test_dfs)} test files")
                    else:
                        logger.error("No valid test CSV files found in directory")
                        test_df = None
                else:
                    logger.error(
                        f"No CSV files found in test directory: {RAW_TEST_FILE}"
                    )
                    test_df = None
            else:
                logger.info(f"Loading test data from file: {RAW_TEST_FILE}")
                test_df = dataset_loader.load_test_data(test_file=RAW_TEST_FILE)
        else:
            logger.error(f"Test data path not found: {RAW_TEST_FILE}")
            test_df = None

        # Check if we have valid data before proceeding
        if test_df is None or len(test_df) == 0:
            logger.error("No valid test data loaded")
            raise ValueError("No valid test data loaded")

        logger.info(f"Loaded {len(train_df)} training samples")
        logger.info(f"Loaded {len(test_df)} test samples")

        # ====================================================================
        # STEP 2: Data Cleaning and Preprocessing
        # ====================================================================
        logger.info("Step 2: Applying data cleaning and preprocessing...")

        # Clean data by removing rows with NaN in critical columns
        critical_columns = ["text", "emotion", "sub-emotion", "intensity"]
        # Only check columns that exist in the dataframes
        train_critical = [col for col in critical_columns if col in train_df.columns]
        test_critical = [col for col in critical_columns if col in test_df.columns]

        initial_train_len = len(train_df)
        initial_test_len = len(test_df)

        train_df = train_df.dropna(subset=train_critical)
        test_df = test_df.dropna(subset=test_critical)

        train_df = train_df.drop_duplicates()
        test_df = test_df.drop_duplicates()

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
        train_df["intensity"] = (
            train_df["intensity"].map(INTENSITY_MAPPING).fillna("mild")
        )
        test_df["intensity"] = (
            test_df["intensity"].map(INTENSITY_MAPPING).fillna("mild")
        )

        # Display class distributions after cleaning
        logger.info("Displaying class distributions after cleaning...")
        log_class_distributions(train_df, output_tasks, "training")
        log_class_distributions(test_df, output_tasks, "test")

        # ====================================================================
        # STEP 3: Initialize Tokenizer and Data Preparation
        # ====================================================================
        logger.info("Step 3: Initializing tokenizer and data preparation...")

        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        data_prep = DataPreparation(
            output_columns=output_tasks,
            tokenizer=tokenizer,
            max_length=MAX_LENGTH,
            batch_size=BATCH_SIZE,
            feature_config=FEATURE_CONFIG,
            encoders_save_dir=ENCODERS_DIR,
        )

        # ====================================================================
        # STEP 4: Process Data and Extract Features
        # ====================================================================
        logger.info("Step 4: Processing data and extracting features...")

        # Prepare data (this will fit encoders, extract features, and create datasets)
        train_dataloader, val_dataloader, test_dataloader = data_prep.prepare_data(
            train_df=train_df.copy(), test_df=test_df.copy(), validation_split=0.1
        )

        logger.info(f"Encoders saved to: {ENCODERS_DIR}")

        # ====================================================================
        # STEP 5: Save Processed Data
        # ====================================================================
        logger.info("Step 5: Saving processed data...")

        # Save processed training data
        if (
            hasattr(data_prep, "train_df_processed")
            and data_prep.train_df_processed is not None
        ):
            train_output_path = os.path.join(PROCESSED_DATA_DIR, "train.csv")
            data_prep.train_df_processed.to_csv(train_output_path, index=False)
            logger.info(f"Processed training data saved to: {train_output_path}")
            logger.info(
                f"Processed training data shape: "
                f"{data_prep.train_df_processed.shape}"
            )
        else:
            logger.warning(
                "Processed training DataFrame not found in DataPreparation object"
            )

        # Save processed test data
        if (
            hasattr(data_prep, "test_df_processed")
            and data_prep.test_df_processed is not None
        ):
            test_output_path = os.path.join(PROCESSED_DATA_DIR, "test.csv")
            data_prep.test_df_processed.to_csv(test_output_path, index=False)
            logger.info(f"Processed test data saved to: {test_output_path}")
            logger.info(
                f"Processed test data shape: {data_prep.test_df_processed.shape}"
            )
        else:
            logger.warning(
                "Processed test DataFrame not found in DataPreparation object"
            )

        # ====================================================================
        # STEP 6: Validation and Summary
        # ====================================================================
        logger.info("Step 6: Validation and summary...")

        # Get encoder information
        num_classes = data_prep.get_num_classes()
        logger.info("Label encoder information:")
        for col, count in num_classes.items():
            logger.info(f"  {col}: {count} classes")
            if hasattr(data_prep.label_encoders[col], "classes_"):
                classes = list(data_prep.label_encoders[col].classes_)
                logger.info(f"    Classes: {classes}")

        # Log feature dimensions
        feature_dim = data_prep.feature_extractor.get_feature_dim()
        logger.info(f"Feature dimension: {feature_dim}")

        # Log dataset sizes
        logger.info("Dataset summary:")
        logger.info(f"  Training samples: {len(train_dataloader.dataset)}")
        val_samples = len(val_dataloader.dataset) if val_dataloader else 0
        logger.info(f"  Validation samples: {val_samples}")
        test_samples = len(test_dataloader.dataset) if test_dataloader else 0
        logger.info(f"  Test samples: {test_samples}")

        logger.info("=== Data Processing Pipeline Completed Successfully ===")

        # ====================================================================
        # STEP 7: Register Data Assets in Azure ML (if requested)
        # ====================================================================
        if args.register_data_assets:
            logger.info("Step 7: Registering processed data as assets in Azure ML...")
            try:
                register_processed_data_assets_from_paths(
                    train_csv_path=os.path.join(PROCESSED_DATA_DIR, "train.csv"),
                    test_csv_path=os.path.join(PROCESSED_DATA_DIR, "test.csv"),
                )
                logger.info("Data asset registration process completed.")
            except ImportError:
                logger.error(
                    "Could not import Azure registration function. "
                    "Make sure azure-ai-ml is installed."
                )
            except Exception as e:
                logger.error(f"Failed to register data assets: {e}")

    except Exception as e:
        logger.error(f"Data processing pipeline failed: {str(e)}")
        logger.error("Full error traceback:", exc_info=True)
        raise


if __name__ == "__main__":
    main()
