"""
DeBERTa-based Multi-Task Emotion Classification Trainer.

This module implements a production-ready training framework for emotion classification
models supporting multiple prediction tasks: emotion, sub-emotion, and intensity levels.

Key Features:
- Multi-task learning with weighted loss functions
- Automatic model checkpointing and validation-based selection
- Azure ML integration for model versioning and deployment
- Comprehensive evaluation metrics and visualization
- Flexible feature engineering pipeline integration

The trainer handles end-to-end model lifecycle from training through evaluation
and deployment, with built-in support for class imbalance and feature fusion.
"""

import argparse
import json
import logging
import os
import pickle
import shutil
import subprocess
import sys
import time
from datetime import timedelta
from typing import Optional

import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn as nn
from dotenv import load_dotenv
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.utils.class_weight import compute_class_weight
from tabulate import tabulate
from termcolor import colored
from torch.optim import AdamW
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup

# Try to import Azure ML logging capabilities
try:
    from azureml.core import Run

    AZUREML_AVAILABLE = True
except ImportError:
    AZUREML_AVAILABLE = False

# Import the local modules
try:
    from .data import DataPreparation
    from .model import ModelLoader
except ImportError:
    from model import ModelLoader

    from data import DataPreparation

# Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


class AzureMLLogger:
    """
    Comprehensive logging class for Azure ML integration.

    Handles both MLflow and Azure ML native logging to ensure metrics
    and artifacts appear correctly in Azure ML job overview.
    """

    def __init__(self):
        """Initialize the Azure ML logger with environment detection."""
        self.is_azure_ml = self._detect_azure_ml_environment()
        self.azure_run = None
        self.mlflow_active = False
        self.artifacts_dir = "outputs"  # Azure ML standard artifacts directory

        # Ensure artifacts directory exists
        os.makedirs(self.artifacts_dir, exist_ok=True)

        if self.is_azure_ml:
            self._setup_azure_ml_logging()

        self._setup_mlflow_logging()

        logger.info(
            f"Azure ML Logger initialized - Azure ML: {self.is_azure_ml}, "
            f"MLflow: {self.mlflow_active}"
        )

    def _detect_azure_ml_environment(self) -> bool:
        """Detect if running in Azure ML environment."""
        azure_env_vars = [
            "AZUREML_RUN_ID",
            "AZUREML_SERVICE_ENDPOINT",
            "AZUREML_RUN_TOKEN",
            "AZUREML_ARM_SUBSCRIPTION",
            "AZUREML_ARM_RESOURCEGROUP",
        ]
        return any(os.getenv(var) for var in azure_env_vars)

    def _setup_azure_ml_logging(self):
        """Setup Azure ML native logging."""
        if not AZUREML_AVAILABLE:
            logger.warning(
                "Azure ML SDK not available, " "skipping native Azure ML logging"
            )
            return

        try:
            # Get the current Azure ML run context
            self.azure_run = Run.get_context()

            # Verify we have a valid run context (not offline)
            if hasattr(self.azure_run, "experiment"):
                logger.info(f"Azure ML run context established: {self.azure_run.id}")
            else:
                logger.warning("Azure ML run context is offline")
                self.azure_run = None

        except Exception as e:
            logger.warning(f"Failed to setup Azure ML logging: {e}")
            self.azure_run = None

    def _setup_mlflow_logging(self):
        """Setup MLflow logging with Azure ML compatibility."""
        try:
            if self.is_azure_ml:
                # In Azure ML, use local file system for MLflow tracking
                tracking_uri = "file:./mlruns"
                mlflow.set_tracking_uri(tracking_uri)
                logger.info(f"MLflow tracking URI set to: {tracking_uri}")

            # Set or create experiment
            experiment_name = os.getenv(
                "MLFLOW_EXPERIMENT_NAME", "emotion-classification-pipeline"
            )

            try:
                mlflow.set_experiment(experiment_name)
                logger.info(f"MLflow experiment set: {experiment_name}")
            except Exception as e:
                logger.warning(f"Failed to set MLflow experiment: {e}")

            self.mlflow_active = True

        except Exception as e:
            logger.warning(f"Failed to setup MLflow: {e}")
            self.mlflow_active = False

    def log_metric(self, key: str, value: float, step: int = None):
        """
        Log metrics to both Azure ML and MLflow.

        Args:
            key: Metric name
            value: Metric value
            step: Step/epoch number
        """
        try:
            # Azure ML native logging
            if self.azure_run:
                if step is not None:
                    # For step-based metrics (per epoch)
                    self.azure_run.log(f"{key}_step", value, step=step)
                else:
                    # For final metrics
                    self.azure_run.log(key, value)

            # MLflow logging
            if self.mlflow_active:
                if step is not None:
                    mlflow.log_metric(key, value, step=step)
                else:
                    mlflow.log_metric(key, value)

        except Exception as e:
            logger.warning(f"Failed to log metric {key}={value}: {e}")

    def log_param(self, key: str, value):
        """Log parameters to both Azure ML and MLflow."""
        try:
            # Azure ML native logging
            if self.azure_run:
                self.azure_run.tag(key, str(value))

            # MLflow logging
            if self.mlflow_active:
                mlflow.log_param(key, value)

        except Exception as e:
            logger.warning(f"Failed to log param {key}={value}: {e}")

    def log_artifact(self, local_path: str, artifact_path: str = None):
        """
        Log artifacts (files/images) to both Azure ML and MLflow.

        Args:
            local_path: Path to local file
            artifact_path: Optional subdirectory in artifacts
        """
        if not os.path.exists(local_path):
            logger.warning(f"Artifact file not found: {local_path}")
            return

        try:
            # Azure ML native logging - upload file to outputs
            if self.azure_run:
                if artifact_path:
                    azure_path = os.path.join(self.artifacts_dir, artifact_path)
                    os.makedirs(os.path.dirname(azure_path), exist_ok=True)
                    # Copy file to outputs directory for Azure ML
                    shutil.copy2(local_path, azure_path)
                    self.azure_run.upload_file(artifact_path, azure_path)
                else:
                    filename = os.path.basename(local_path)
                    azure_path = os.path.join(self.artifacts_dir, filename)
                    shutil.copy2(local_path, azure_path)
                    self.azure_run.upload_file(filename, azure_path)

            # MLflow logging
            if self.mlflow_active:
                mlflow.log_artifact(local_path, artifact_path)

        except Exception as e:
            logger.warning(f"Failed to log artifact {local_path}: {e}")

    def log_image(self, image_path: str, name: str = None):
        """
        Log image specifically for Azure ML visualization.

        Args:
            image_path: Path to image file
            name: Display name for the image
        """
        if not os.path.exists(image_path):
            logger.warning(f"Image file not found: {image_path}")
            return

        try:
            display_name = name or os.path.splitext(os.path.basename(image_path))[0]

            # Azure ML native image logging
            if self.azure_run:
                # Log as image for visualization in Azure ML
                self.azure_run.log_image(display_name, path=image_path)

                # Also upload to outputs for persistence
                output_path = os.path.join(
                    self.artifacts_dir, "images", os.path.basename(image_path)
                )
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy2(image_path, output_path)

            # MLflow logging
            if self.mlflow_active:
                mlflow.log_artifact(image_path, "images")

        except Exception as e:
            logger.warning(f"Failed to log image {image_path}: {e}")

    def log_table(self, name: str, data: dict):
        """Log table data to Azure ML."""
        try:
            if self.azure_run:
                self.azure_run.log_table(name, data)
        except Exception as e:
            logger.warning(f"Failed to log table {name}: {e}")

    def start_logging(self, run_name: str = None):
        """Start logging session."""
        try:
            if self.mlflow_active and not mlflow.active_run():
                mlflow.start_run(run_name=run_name)
                logger.info("MLflow run started")
        except Exception as e:
            logger.warning(f"Failed to start MLflow run: {e}")

    def end_logging(self):
        """End logging session."""
        try:
            if self.mlflow_active and mlflow.active_run():
                mlflow.end_run()
                logger.info("MLflow run ended")
        except Exception as e:
            logger.warning(f"Failed to end MLflow run: {e}")

    def complete_run(self, status: str = "COMPLETED"):
        """Complete the Azure ML run."""
        try:
            if self.azure_run:
                self.azure_run.complete()
                logger.info("Azure ML run completed")
        except Exception as e:
            logger.warning(f"Failed to complete Azure ML run: {e}")

    def create_evaluation_plots(
        self, test_preds, test_labels, test_metrics, evaluation_dir, output_tasks
    ):
        """
        Create comprehensive evaluation plots for Azure ML visualization.

        Args:
            test_preds: Dictionary of test predictions per task
            test_labels: Dictionary of test labels per task
            test_metrics: Dictionary of test metrics per task
            evaluation_dir: Directory to save plots
            output_tasks: List of output tasks
        """
        try:

            # Set style for better plots
            plt.style.use("default")
            sns.set_palette("husl")

            # Create plots for each task
            for task in output_tasks:
                if task not in test_preds or task not in test_labels:
                    continue

                task_preds = test_preds[task]
                task_labels = test_labels[task]

                # 1. Confusion Matrix
                cm = confusion_matrix(task_labels, task_preds)

                plt.figure(figsize=(10, 8))
                sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
                plt.title(f"{task.capitalize()} - Confusion Matrix")
                plt.ylabel("True Label")
                plt.xlabel("Predicted Label")

                cm_path = os.path.join(evaluation_dir, f"{task}_confusion_matrix.png")
                plt.tight_layout()
                plt.savefig(cm_path, dpi=300, bbox_inches="tight")
                plt.close()

                # 2. Performance Metrics Bar Chart
                if task in test_metrics:
                    metrics_data = test_metrics[task]
                    metric_names = []
                    metric_values = []

                    for key, value in metrics_data.items():
                        # Use the actual keys returned by calculate_metrics
                        valid_metrics = ["acc", "f1", "prec", "rec"]
                        if key in valid_metrics and isinstance(value, (int, float)):
                            # Create display names for the metrics
                            display_name = {
                                "acc": "Accuracy",
                                "f1": "F1 Score",
                                "prec": "Precision",
                                "rec": "Recall",
                            }.get(key, key.replace("_", " ").title())
                            metric_names.append(display_name)
                            metric_values.append(value)

                    if metric_names and metric_values:
                        plt.figure(figsize=(10, 6))
                        colors = ["skyblue", "lightgreen", "lightcoral", "gold"]
                        colors = colors[: len(metric_names)]
                        bars = plt.bar(metric_names, metric_values, color=colors)
                        plt.title(f"{task.capitalize()} - Performance Metrics")
                        plt.ylabel("Score")
                        plt.ylim(0, 1)

                        # Add value labels on bars
                        for bar, value in zip(bars, metric_values):
                            plt.text(
                                bar.get_x() + bar.get_width() / 2,
                                bar.get_height() + 0.01,
                                f"{value:.3f}",
                                ha="center",
                                va="bottom",
                            )

                        metrics_path = os.path.join(
                            evaluation_dir, f"{task}_metrics_chart.png"
                        )
                        plt.tight_layout()
                        plt.savefig(metrics_path, dpi=300, bbox_inches="tight")
                        plt.close()

            # 3. Overall Performance Comparison
            plt.figure(figsize=(12, 8))
            tasks = [task for task in output_tasks if task in test_metrics]

            if tasks:
                f1_scores = []
                accuracy_scores = []

                for task in tasks:
                    task_metrics = test_metrics[task]
                    # Use the actual keys returned by calculate_metrics
                    f1_score = task_metrics.get("f1", 0)
                    acc_score = task_metrics.get("acc", 0)
                    f1_scores.append(f1_score)
                    accuracy_scores.append(acc_score)

                x = np.arange(len(tasks))
                width = 0.35

                plt.bar(x - width / 2, f1_scores, width, label="F1 Score", alpha=0.8)
                plt.bar(
                    x + width / 2, accuracy_scores, width, label="Accuracy", alpha=0.8
                )

                plt.xlabel("Tasks")
                plt.ylabel("Score")
                plt.title("Overall Performance Comparison Across Tasks")
                plt.xticks(x, [task.replace("_", " ").title() for task in tasks])
                plt.legend()
                plt.ylim(0, 1)

                # Add value labels
                for i, (f1, acc) in enumerate(zip(f1_scores, accuracy_scores)):
                    plt.text(
                        i - width / 2, f1 + 0.01, f"{f1:.3f}", ha="center", va="bottom"
                    )
                    plt.text(
                        i + width / 2,
                        acc + 0.01,
                        f"{acc:.3f}",
                        ha="center",
                        va="bottom",
                    )

                overall_path = os.path.join(evaluation_dir, "overall_performance.png")
                plt.tight_layout()
                plt.savefig(overall_path, dpi=300, bbox_inches="tight")
                plt.close()

            logger.info(f"Evaluation plots saved to {evaluation_dir}")

        except Exception as e:
            logger.warning(f"Failed to create evaluation plots: {e}")

    def log_evaluation_artifacts(self, evaluation_dir):
        """
        Log all evaluation artifacts to Azure ML for visualization.

        Args:
            evaluation_dir: Directory containing evaluation artifacts
        """
        try:
            if not os.path.exists(evaluation_dir):
                logger.warning(f"Evaluation directory does not exist: {evaluation_dir}")
                return

            # Log all PNG files as images
            for filename in os.listdir(evaluation_dir):
                file_path = os.path.join(evaluation_dir, filename)

                if filename.endswith(".png"):
                    # Log as image for Azure ML visualization
                    display_name = (
                        filename.replace(".png", "").replace("_", " ").title()
                    )
                    self.log_image(file_path, name=display_name)

                elif filename.endswith((".json", ".csv")):
                    # Log other files as artifacts
                    self.log_artifact(file_path, f"evaluation/{filename}")

            logger.info("Evaluation artifacts logged to Azure ML")

        except Exception as e:
            logger.warning(f"Failed to log evaluation artifacts: {e}")


class CustomTrainer:
    """
    Production-ready trainer for multi-task emotion classification using DeBERTa.

    Manages the complete training lifecycle including data loading, model training,
    validation, checkpointing, and evaluation. Supports flexible task configuration
    and automatic model promotion based on performance thresholds.

    Key Capabilities:
    - Multi-task learning with weighted loss aggregation
    - Automatic best model selection via validation metrics
    - Feature engineering pipeline integration
    - Azure ML model versioning and deployment
    - Class imbalance handling through weighted loss functions

    Thread Safety: Not thread-safe. Use separate instances for concurrent training.
    """

    def __init__(
        self,
        model,
        train_dataloader,
        val_dataloader,
        test_dataloader,
        device,
        test_set_df,
        class_weights_tensor,
        encoders_dir,
        output_tasks=None,
        learning_rate=2e-5,
        weight_decay=0.01,
        epochs=1,
        feature_config=None,
    ):
        """
        Initialize the emotion classification trainer.

        Sets up training infrastructure, loads encoders, validates model dimensions,
        and configures feature engineering pipeline. Automatically determines feature
        dimensions from training data.

        Args:
            model: DeBERTa classifier instance with multi-task heads
            train_dataloader: PyTorch DataLoader for training data
            val_dataloader: PyTorch DataLoader for validation data
            test_dataloader: PyTorch DataLoader for test data
            device: PyTorch device (cuda/cpu) for model execution
            test_set_df: Pandas DataFrame containing original test data with text
            class_weights_tensor: Tensor or dict of class weights for imbalanced data
            encoders_dir: Directory path containing label encoder pickle files
            output_tasks: List of pred tasks ['emotion', 'sub_emotion', 'intensity']
            learning_rate: AdamW optimizer learning rate (default: 2e-5)
            weight_decay: L2 regularization coefficient (default: 0.01)
            epochs: Number of training epochs (default: 1)
            feature_config: Dict specifying which engineered features to use

        Raises:
            FileNotFoundError: If encoder files are missing from encoders_dir
            ValueError: If model dimensions don't match encoder classes

        Side Effects:
            - Loads and validates label encoders
            - Configures task-specific loss weights
            - Logs initialization status and warnings
        """

        # Initializations
        self.model = model
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader
        self.test_dataloader = test_dataloader
        self.device = device
        self.test_set_df = test_set_df
        self.class_weights_tensor = class_weights_tensor
        self.output_tasks = output_tasks or ["emotion", "sub_emotion", "intensity"]
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.epochs = epochs

        # Initialize Azure ML logger
        self.azure_logger = AzureMLLogger()

        # Set feature configuration if not provided
        self.feature_config = feature_config or {
            "pos": False,
            "textblob": False,
            "vader": False,
            "tfidf": True,
            "emolex": True,
        }

        # Load the encoders for each task
        self._load_encoders(encoders_dir)

        # Determine feature dimensions from training data
        if self.train_dataloader:
            self.feature_dim = self._get_feature_dim()

        # Fallback strategies for evaluation-only scenarios
        else:

            # If model has a feature_dim attribute, use it
            if hasattr(model, "feature_dim"):
                self.feature_dim = model.feature_dim

            # If train_dataloader is not available, check test_dataloader
            elif self.test_dataloader:
                first_batch = next(iter(self.test_dataloader))
                if "features" in first_batch:
                    self.feature_dim = first_batch["features"].shape[-1]
                else:
                    self.feature_dim = 0

            # If no dataloaders are available, set feature_dim to 0
            else:
                self.feature_dim = 0

        # Define task-specific loss weights for multi-task learning
        # Higher weights for primary tasks, lower for auxiliary tasks
        self.task_weights = {
            "emotion": 1.0 if "emotion" in self.output_tasks else 0.0,
            "sub_emotion": 0.8 if "sub_emotion" in self.output_tasks else 0.0,
            "intensity": 0.2 if "intensity" in self.output_tasks else 0.0,
        }

    def _get_feature_dim(self):
        """
        Extract feature dimensionality from training data.

        Inspects the first batch of training data to determine the size of
        engineered features for model initialization. This ensures the model's
        feature fusion layer has the correct input dimensions.

        Returns:
            int: Feature vector dimensionality, or 0 if features unavailable

        Side Effects:
            - Consumes one batch from training dataloader iterator
            - Logs warnings if features are missing or malformed
        """

        # If train_dataloader is not set, return 0
        if not self.train_dataloader:
            return 0

        # Error handling
        try:

            # Get the first batch from the train_dataloader
            first_batch = next(iter(self.train_dataloader))

            # If "features" key is not present or is None, log and return 0
            if "features" not in first_batch or first_batch["features"] is None:
                logger.warning(
                    "'features' key not found or is None in the first batch"
                    " of train_dataloader. Assuming 0 feature_dim or check data prep."
                )
                return 0

            # If "features" is present, return its dimensionality
            feature_dim = first_batch["features"].shape[-1]

            return feature_dim

        # Handle cases where the first batch is empty or malformed
        except Exception as e:
            logger.error(f"Error getting feature dimension from train_dataloader: {e}")
            return 0

    def _load_encoders(self, encoders_dir):
        """
        Load label encoders for all configured prediction tasks.

        Loads scikit-learn LabelEncoder instances from pickle files to enable
        conversion between string labels and numeric indices. Each encoder
        maps task-specific class names to consecutive integers.

        Args:
            encoders_dir: Directory containing encoder pickle files
                         Expected files: emotion_encoder.pkl, sub_emotion_encoder.pkl,
                         intensity_encoder.pkl

        Raises:
            FileNotFoundError: If required encoder files are missing
            Exception: If pickle deserialization fails

        Side Effects:
            - Sets instance attributes: emotion_encoder, sub_emotion_encoder, etc.
            - Logs successful loads and any errors encountered
        """

        # Error handling
        try:

            # Load encoder for each task
            if "emotion" in self.output_tasks:
                with open(os.path.join(encoders_dir, "emotion_encoder.pkl"), "rb") as f:
                    self.emotion_encoder = pickle.load(f)
            if "sub_emotion" in self.output_tasks:
                with open(
                    os.path.join(encoders_dir, "sub_emotion_encoder.pkl"), "rb"
                ) as f:
                    self.sub_emotion_encoder = pickle.load(f)
            if "intensity" in self.output_tasks:
                with open(
                    os.path.join(encoders_dir, "intensity_encoder.pkl"), "rb"
                ) as f:
                    self.intensity_encoder = pickle.load(f)

        # If any encoder file is missing, raise an error
        except Exception as e:
            logger.error(f"Error loading encoders: {e}")
            raise

    def setup_training(self):
        """
        Initialize training components for multi-task learning.

        Configures loss functions, optimizer, and learning rate scheduler
        for all active prediction tasks. Sets up class-weighted losses
        for imbalanced datasets and linear warmup scheduling.

        Returns:
            tuple: (criterion_dict, optimizer, scheduler) where:
                - criterion_dict: Task-specific CrossEntropyLoss functions
                - optimizer: AdamW optimizer with L2 regularization
                - scheduler: Linear warmup learning rate scheduler

        Side Effects:
            - Moves class weights to appropriate device
            - Logs successful setup completion
        """

        # Initialize a dictionary to hold loss functions for each task
        criterion_dict = {}

        # Calculate loss for "emotion" task
        if "emotion" in self.output_tasks:
            actual_emotion_weights = None
            if self.class_weights_tensor is not None:
                if isinstance(self.class_weights_tensor, dict):
                    tensor_for_emotion = self.class_weights_tensor.get("emotion")
                    if (tensor_for_emotion is not None) and hasattr(
                        tensor_for_emotion, "to"
                    ):
                        actual_emotion_weights = tensor_for_emotion.to(self.device)
                elif hasattr(self.class_weights_tensor, "to"):
                    actual_emotion_weights = self.class_weights_tensor.to(self.device)
            criterion_dict["emotion"] = nn.CrossEntropyLoss(
                weight=actual_emotion_weights
            )

        # Calculate loss for "sub_emotion" task
        if "sub_emotion" in self.output_tasks:
            criterion_dict["sub_emotion"] = nn.CrossEntropyLoss()

        # Calculate loss for "intensity" task
        if "intensity" in self.output_tasks:
            criterion_dict["intensity"] = nn.CrossEntropyLoss()

        # Initialize optimizer
        optimizer = AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay,
        )

        # Calculate total training steps for scheduler
        total_steps = len(self.train_dataloader) * self.epochs

        # Initialize learning rate scheduler with linear warmup
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=0.1 * total_steps,
            num_training_steps=total_steps,
        )

        logger.info("Training setup complete: criterion, optimizer, scheduler.")

        return criterion_dict, optimizer, scheduler

    def train_epoch(self, criterion_dict, optimizer, scheduler):
        """
        Execute one complete training epoch across all batches.

        Performs forward pass, loss computation, backpropagation, and optimizer
        updates for all configured tasks. Collects predictions and ground truth
        labels for comprehensive metric calculation.

        Args:
            criterion_dict: Task-specific loss functions (from setup_training)
            optimizer: AdamW optimizer instance
            scheduler: Learning rate scheduler instance

        Returns:
            tuple: (avg_train_loss, train_metrics_epoch) where:
                - avg_train_loss: Mean loss across all batches
                - train_metrics_epoch: Dict of metrics per task

        Side Effects:
            - Updates model parameters via backpropagation
            - Advances learning rate scheduler
            - Logs training progress via tqdm progress bar
        """

        # Set model to training mode
        self.model.train()

        # Initialize loss and metrics storage
        train_loss = 0

        # Collect predictions and labels
        all_preds_train = {task: [] for task in self.output_tasks}
        all_labels_train = {task: [] for task in self.output_tasks}

        # Loop over training batches
        for batch_idx, batch in enumerate(
            tqdm(self.train_dataloader, desc="Training", ncols=120, colour="green")
        ):

            # Zero gradients for the optimizer
            optimizer.zero_grad()

            # Move input tensors to the appropriate device
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            features = batch.get("features")

            # Move features to device if present, if not set to None
            if features is not None and self.feature_dim > 0:
                features = features.to(self.device)
            else:
                features = None

            # Forward pass through the model
            outputs = self.model(
                input_ids, attention_mask=attention_mask, features=features
            )

            # Prepare labels for each task
            labels = {}
            for task in self.output_tasks:
                task_label_key = f"{task}_label"
                if task_label_key in batch:
                    labels[task] = batch[task_label_key].to(self.device)
                    all_labels_train[task].extend(batch[task_label_key].cpu().numpy())
                else:
                    logger.error(f"Label key '{task_label_key}' not found in batch.")
                    logger.error(f" Available keys: {list(batch.keys())}")
                    continue

            # Collect predictions for each task
            for task in self.output_tasks:
                if (
                    isinstance(outputs, dict)
                    and (task in outputs)
                    and (outputs[task] is not None)
                ):
                    preds = torch.argmax(outputs[task], dim=1).cpu().numpy()
                    all_preds_train[task].extend(preds)
                elif not (isinstance(outputs, dict) and task in outputs):
                    logger.warning(
                        f"Task '{task}' not in model outputs \
                        or outputs is not a dict."
                    )

            # Calculate loss for each task
            current_loss = torch.tensor(0.0, device=self.device, requires_grad=True)
            valid_task_loss_calculated = False
            for task in self.output_tasks:
                if (
                    isinstance(outputs, dict)
                    and (task in outputs)
                    and isinstance(labels, dict)
                    and (task in labels)
                ):
                    if (outputs[task] is not None) and (labels[task] is not None):
                        task_loss = criterion_dict[task](outputs[task], labels[task])
                        current_loss = current_loss + (
                            self.task_weights[task] * task_loss
                        )
                        valid_task_loss_calculated = True

            # If at least one task loss was calculated, perform backpropagation
            if valid_task_loss_calculated:
                current_loss.backward()
                optimizer.step()
                scheduler.step()
                train_loss += current_loss.item()
            else:
                logger.warning("No valid task loss calculated. Skipping backward pass.")

        # Calculate average training loss for the epoch
        avg_train_loss = (
            train_loss / len(self.train_dataloader)
            if len(self.train_dataloader) > 0
            else 0
        )
        logger.debug(f"Epoch training loss: {avg_train_loss}")

        # Calculate training metrics for the epoch
        train_metrics_epoch = {}
        for task in self.output_tasks:
            if all_labels_train[task] and all_preds_train[task]:
                train_metrics_epoch[task] = self.calculate_metrics(
                    all_preds_train[task],
                    all_labels_train[task],
                    task_name=f"Train {task}",
                )
            else:
                logger.warning(
                    f"No training data/predictions collected for task '{task}' "
                    f"in epoch. Metrics will be zero."
                )
                train_metrics_epoch[task] = {
                    "acc": 0,
                    "f1": 0,
                    "prec": 0,
                    "rec": 0,
                    "report": "No data for training metrics",
                }

        return avg_train_loss, train_metrics_epoch

    def evaluate(self, dataloader, criterion_dict, is_test=False):
        """
        Evaluate model performance on validation or test data.

        Runs inference on provided dataset without gradient computation,
        collecting predictions and computing loss for all active tasks.

        Args:
            dataloader: PyTorch DataLoader containing evaluation data
            criterion_dict: Task-specific loss functions for loss computation
            is_test: Boolean flag for logging context (test vs validation)

        Returns:
            tuple: (avg_eval_loss, all_preds, all_labels) where:
                - avg_eval_loss: Mean loss across all evaluation batches
                - all_preds: Dict mapping task names to prediction lists
                - all_labels: Dict mapping task names to ground truth lists

        Side Effects:
            - Sets model to evaluation mode (disables dropout/batch norm)
            - Logs evaluation progress via tqdm progress bar
        """

        # Set model to evaluation mode
        self.model.eval()

        # Initialize loss for evaluation
        eval_loss = 0

        # Collect predictions and labels for all tasks
        all_preds = {task: [] for task in self.output_tasks}
        all_labels = {task: [] for task in self.output_tasks}

        # Turn off gradient computation for evaluation
        with torch.no_grad():

            # Loop over evaluation batches
            for batch in tqdm(
                dataloader,
                desc="Testing" if is_test else "Validation",
                ncols=120,
                colour="yellow" if is_test else "blue",
            ):

                # Move input tensors to the appropriate device
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                features = (
                    batch["features"].to(self.device)
                    if "features" in batch and self.feature_dim > 0
                    else None
                )

                # Prepare true labels for each task
                true_labels_batch = {}
                for task in self.output_tasks:
                    task_label_key = f"{task}_label"
                    if task_label_key in batch:
                        true_labels_batch[task] = batch[task_label_key].to(self.device)
                    else:
                        logger.error(
                            f"Task label key '{task_label_key}' not found in "
                            f"val/test batch. Available keys: {list(batch.keys())}"
                        )
                        true_labels_batch[task] = torch.empty(0, device=self.device)

                # Feed inputs to the model
                model_outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    features=features,
                )

                # Handle single output case by converting to dict
                if len(self.output_tasks) == 1 and not isinstance(
                    model_outputs, (list, tuple)
                ):
                    task_key = self.output_tasks[0]
                    model_outputs = {task_key: model_outputs}

                # Initialize loss
                loss = 0

                # Loop over each task
                for task_idx, task in enumerate(self.output_tasks):

                    # Get task output and labels
                    task_output = model_outputs[task]
                    task_labels = true_labels_batch[task]

                    # Calculate loss
                    task_loss = criterion_dict[task](task_output, task_labels)

                    # Accumulate weighted loss
                    loss += self.task_weights[task] * task_loss

                    # Collect predictions and labels
                    preds = torch.argmax(task_output, dim=1).cpu().numpy()

                    # Store predictions and labels
                    all_preds[task].extend(preds)
                    all_labels[task].extend(task_labels.cpu().numpy())

                # Accumulate total evaluation loss
                eval_loss += loss.item()

        # Calculate average evaluation loss
        avg_eval_loss = eval_loss / len(dataloader)
        logger.debug(f"{'Test' if is_test else 'Validation'} loss: {avg_eval_loss}")

        return avg_eval_loss, all_preds, all_labels

    def train_and_evaluate(
        self,
        trained_model_output_dir,
        metrics_output_file,
        weights_dir_base="models/weights",
    ):
        """
        Execute complete training pipeline with validation-based model selection.

        Orchestrates the full training workflow including epoch iteration,
        validation evaluation, best model tracking, and artifact persistence.
        Integrates with MLflow for experiment tracking and Azure ML for model
        deployment.

        Args:
            trained_model_output_dir: Directory path for saving the best model
            metrics_output_file: JSON file path for training metrics storage
            weights_dir_base: Base directory for temporary model checkpoints

        Returns:
            dict: Best validation F1 scores for each task from optimal epoch

        Side Effects:
            - Creates temporary directories for model checkpoints
            - Logs training progress and metrics to MLflow
            - Saves model configuration and state dict files
            - Attempts Azure ML model upload with auto-promotion
            - Cleans up temporary checkpoint files after completion
        """

        # Setup training components
        criterion_dict, optimizer, scheduler = self.setup_training()

        # Start Azure ML logging session
        self.azure_logger.start_logging(run_name="emotion-classification-training")

        # Log hyperparameters
        self.azure_logger.log_param("learning_rate", self.learning_rate)
        self.azure_logger.log_param("epochs", self.epochs)
        self.azure_logger.log_param("output_tasks", str(self.output_tasks))
        self.azure_logger.log_param("feature_config", str(self.feature_config))

        # Initialize best validation scores and paths
        best_val_f1s = {task: 0.0 for task in self.output_tasks}
        best_overall_val_f1 = 0.0
        best_model_epoch_path = None

        # Ensure the temporary weights directory exists
        run_weights_dir = os.path.join(weights_dir_base, "current_run_temp_weights")
        if os.path.exists(run_weights_dir):
            shutil.rmtree(run_weights_dir)
        os.makedirs(run_weights_dir, exist_ok=True)

        # Training loop with comprehensive logging
        for epoch in range(self.epochs):
            logger.info(f"=== Epoch {epoch + 1}/{self.epochs} ===")

            # Training phase
            avg_train_loss, train_metrics = self.train_epoch(
                criterion_dict, optimizer, scheduler
            )

            # Validation phase
            avg_val_loss, val_preds, val_labels = self.evaluate(
                self.val_dataloader, criterion_dict, is_test=False
            )

            # Calculate validation metrics
            val_metrics = {}
            for task in self.output_tasks:
                val_metrics[task] = self.calculate_metrics(
                    val_preds[task], val_labels[task], task_name=task
                )

            # Log epoch metrics to Azure ML
            step = epoch + 1

            # Log losses
            self.azure_logger.log_metric("train_loss", avg_train_loss, step=step)
            self.azure_logger.log_metric("val_loss", avg_val_loss, step=step)

            # Log training metrics (filter out non-numeric values)
            for task in self.output_tasks:
                for metric_name, metric_value in train_metrics[task].items():
                    # Only log numeric metrics, skip string reports
                    is_numeric = isinstance(metric_value, (int, float))
                    is_valid = is_numeric and not np.isnan(metric_value)
                    if is_valid:
                        self.azure_logger.log_metric(
                            f"train_{task}_{metric_name}", metric_value, step=step
                        )

            # Log validation metrics (filter out non-numeric values)
            for task in self.output_tasks:
                for metric_name, metric_value in val_metrics[task].items():
                    # Only log numeric metrics, skip string reports
                    is_numeric = isinstance(metric_value, (int, float))
                    is_valid = is_numeric and not np.isnan(metric_value)
                    if is_valid:
                        self.azure_logger.log_metric(
                            f"val_{task}_{metric_name}", metric_value, step=step
                        )

            # Print metrics tables
            self.print_metrics(train_metrics, "Train", loss=avg_train_loss)
            self.print_metrics(val_metrics, "Val", loss=avg_val_loss)

            # Calculate overall validation F1 (weighted average)
            overall_val_f1 = np.mean(
                [val_metrics[task]["f1"] for task in self.output_tasks]
            )

            # Log overall F1 score
            self.azure_logger.log_metric("val_overall_f1", overall_val_f1, step=step)

            # Model checkpointing logic
            if overall_val_f1 > best_overall_val_f1:
                best_overall_val_f1 = overall_val_f1
                best_val_f1s = {
                    task: val_metrics[task]["f1"] for task in self.output_tasks
                }

                # Save best model checkpoint
                epoch_checkpoint_path = os.path.join(
                    run_weights_dir, f"best_model_epoch_{epoch + 1}.pt"
                )
                torch.save(self.model.state_dict(), epoch_checkpoint_path)
                best_model_epoch_path = epoch_checkpoint_path

                logger.info(
                    f"New best model saved at epoch {epoch + 1} with overall F1: \
                        {overall_val_f1:.4f}"
                )

        # Final model evaluation and logging
        if best_model_epoch_path:
            # Load best model for final evaluation
            self.model.load_state_dict(
                torch.load(best_model_epoch_path, weights_only=False)
            )
            logger.info("Loaded best model for final evaluation")

            # Final test evaluation
            logger.info("=== Final Test Evaluation ===")
            test_loss, test_preds, test_labels = self.evaluate(
                self.test_dataloader, criterion_dict, is_test=True
            )

            # Calculate test metrics
            test_metrics = {}
            for task in self.output_tasks:
                test_metrics[task] = self.calculate_metrics(
                    test_preds[task], test_labels[task], task_name=task
                )

            # Log final test metrics (filter out non-numeric values)
            for task in self.output_tasks:
                for metric_name, metric_value in test_metrics[task].items():
                    # Only log numeric metrics, skip string reports
                    is_numeric = isinstance(metric_value, (int, float))
                    is_valid = is_numeric and not np.isnan(metric_value)
                    if is_valid:
                        self.azure_logger.log_metric(
                            f"test_{task}_{metric_name}", metric_value
                        )

            # Print final test metrics
            self.print_metrics(test_metrics, "Test", loss=test_loss)

            # Save final model
            final_model_path = os.path.join(
                trained_model_output_dir, "dynamic_weights.pt"
            )
            os.makedirs(trained_model_output_dir, exist_ok=True)
            torch.save(self.model.state_dict(), final_model_path)

            # Save model config for deployment
            model_config = {
                "model_name": self.model.model_name,
                "feature_dim": self.model.feature_dim,
                "num_classes": self.model.num_classes,
                "hidden_dim": self.model.hidden_dim,
                "dropout": self.model.dropout_prob,
            }
            config_path = os.path.join(trained_model_output_dir, "model_config.json")
            with open(config_path, "w") as f:
                json.dump(model_config, f, indent=4)
            logger.info(f"Model config for deployment saved to {config_path}")

            # Generate and log evaluation visualizations
            evaluation_dir = os.path.join(
                os.path.dirname(trained_model_output_dir), "evaluation"
            )
            os.makedirs(evaluation_dir, exist_ok=True)

            # Create comprehensive evaluation plots
            self.azure_logger.create_evaluation_plots(
                test_preds, test_labels, test_metrics, evaluation_dir, self.output_tasks
            )

            # Log all generated plots as artifacts
            self.azure_logger.log_evaluation_artifacts(evaluation_dir)

            # Save comprehensive metrics
            final_metrics = {
                "best_validation_f1s": best_val_f1s,
                "best_overall_validation_f1": best_overall_val_f1,
                "test_metrics": test_metrics,
                "training_config": {
                    "learning_rate": self.learning_rate,
                    "epochs": self.epochs,
                    "output_tasks": self.output_tasks,
                    "feature_config": self.feature_config,
                },
            }

            metrics_file = os.path.join(evaluation_dir, "training_metrics.json")
            with open(metrics_file, "w") as f:
                json.dump(final_metrics, f, indent=2)

            self.azure_logger.log_artifact(
                metrics_file, "metrics/training_metrics.json"
            )
        # Update monitoring system with new training metrics
        try:
            from .monitoring import metrics_collector

            # Prepare metrics for monitoring update
            monitoring_metrics = {}
            for task_name, f1_val in best_val_f1s.items():
                monitoring_metrics[task_name] = {"f1": f1_val}

            # Also add test metrics if available
            if test_metrics:
                for task_name, task_metrics in test_metrics.items():
                    if task_name in monitoring_metrics:
                        acc_val = task_metrics.get("acc", 0.0)
                        monitoring_metrics[task_name]["accuracy"] = acc_val
                    else:
                        monitoring_metrics[task_name] = {
                            "accuracy": task_metrics.get("acc", 0.0),
                            "f1": task_metrics.get("f1", 0.0),
                        }

            # Update the monitoring system
            metrics_collector.update_model_performance(monitoring_metrics)
            task_list = list(monitoring_metrics.keys())
            print("📊 Updated monitoring system with training metrics")
            print(f"   Tasks: {task_list}")

        except ImportError:
            print("⚠️ Monitoring system not available - skipping metrics update")
        except Exception as e:
            print(f"⚠️ Failed to update monitoring system: {e}")
        else:
            logger.warning("Best model epoch path not found. Skipping evaluation.")

        # End logging session
        self.azure_logger.end_logging()

        # Cleanup temporary files
        if os.path.exists(run_weights_dir):
            shutil.rmtree(run_weights_dir)

        return best_val_f1s

    def evaluate_final_model(self, model_path, evaluation_output_dir):
        """
        Perform comprehensive evaluation of a trained model on test data.

        Loads a trained model from disk, runs inference on the test dataset,
        and generates detailed evaluation reports including per-sample predictions,
        accuracy metrics, and exported results for analysis.

        Args:
            model_path: File path to saved model state dict (.pt file)
            evaluation_output_dir: Directory for saving evaluation artifacts

        Returns:
            pd.DataFrame: Comprehensive results with columns:
                - text: Original input text samples
                - true_{task}: Ground truth labels for each task
                - pred_{task}: Model predictions for each task
                - {task}_correct: Boolean correctness per task
                - all_correct: Boolean indicating all tasks correct (if multi-task)

        Raises:
            FileNotFoundError: If model file doesn't exist at specified path
            RuntimeError: If model loading or inference fails

        Side Effects:
            - Loads model weights and sets to evaluation mode
            - Creates evaluation output directory if it doesn't exist
            - Saves detailed evaluation report as CSV file
            - Logs progress and any warnings encountered
        """

        # If model path doesn't exist, raise an error
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}")
            raise FileNotFoundError(f"Model file not found at {model_path}")

        # Error handling
        try:

            # # Load the model config file if it exists
            # model_config_path = os.path.join(
            #     os.path.dirname(model_path), "model_config.json"
            # )
            # if os.path.exists(model_config_path):
            #     with open(model_config_path, 'r') as f:
            #         model_config = json.load(f)

            # Load state_dict and handle key remapping for bert->deberta conversion
            state_dict = torch.load(
                model_path, map_location=self.device, weights_only=False
            )

            # Create a new state_dict with corrected keys
            new_state_dict = {}
            for k, v in state_dict.items():
                if k.startswith("bert."):
                    new_key = "deberta." + k[len("bert.") :]
                    new_state_dict[new_key] = v
                else:
                    new_state_dict[k] = v

            # Load the state_dict into the model
            self.model.load_state_dict(new_state_dict)

            # Move model to  device
            self.model.to(self.device)

            # Set model to evaluation mode
            self.model.eval()

            logger.info("Model loaded and set to evaluation mode.")

        # Raise error if model loading fails
        except Exception as e:
            logger.error(f"Error loading model state_dict from {model_path}: {e}")
            raise

        # Initialize lists for predictions and labels
        predictions = {task: [] for task in self.output_tasks}
        labels = {task: [] for task in self.output_tasks}

        # Turn off gradient computation for evaluation
        with torch.no_grad():

            # Loop over test batches
            for batch in tqdm(
                self.test_dataloader, desc="Final Testing", ncols=120, colour="green"
            ):

                # Move tensors to the appropriate device
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                features = (
                    batch["features"].to(self.device)
                    if "features" in batch and self.feature_dim > 0
                    else None
                )

                # Initialize a dictionary to hold true labels for each task
                true_labels_batch = {}

                # Loop over output tasks
                for task in self.output_tasks:

                    # Construct the task-specific label key
                    task_label_key = f"{task}_label"

                    # If the task label key exists in the batch,
                    if task_label_key in batch:

                        # Store original labels
                        labels[task].extend(batch[task_label_key].cpu().numpy())
                        true_labels_batch[task] = batch[task_label_key].to(self.device)

                    # If the task label key is missing, log an error
                    else:
                        logger.error(
                            f"Task label key '{task_label_key}' not \
                            found in test batch. Available keys: {list(batch.keys())}"
                        )
                        continue

                # Only proceed with model prediction if we have at least one valid task
                if not true_labels_batch:
                    logger.warning("No valid task labels found in batch. Skipping it.")
                    continue

                # Feed inputs to the model
                model_outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    features=features,
                )

                # Handle single output case by converting to dict
                if len(self.output_tasks) == 1 and not isinstance(
                    model_outputs, (list, tuple)
                ):
                    task_key = self.output_tasks[0]
                    model_outputs = {task_key: model_outputs}

                # Loop over each task to collect predictions into the predictions dict
                for task_idx, task in enumerate(self.output_tasks):
                    task_output = model_outputs[task]
                    preds = torch.argmax(task_output, dim=1).cpu().numpy()
                    predictions[task].extend(preds)

        logger.info("Predictions generated.")

        # If test_set_df is not provided, create a placeholder text column
        if "text" not in self.test_set_df.columns:
            num_test_samples = (
                len(predictions[self.output_tasks[0]]) if self.output_tasks else 0
            )
            results = {"text": [f"Sample_{i}" for i in range(num_test_samples)]}

        # If test_set_df is provided, use its 'text' column
        else:
            num_predicted_samples = len(predictions[self.output_tasks[0]])
            results = {
                "text": self.test_set_df["text"][:num_predicted_samples].tolist()
            }

        # Loop over each task
        for task in self.output_tasks:

            # Get the encoder for the task
            encoder = getattr(self, f"{task}_encoder", None)

            # If encoder exists, perform inverse transformation and store results
            if encoder:
                labels_for_inverse = [int(lbl) for lbl in labels[task]]
                predictions_for_inverse = [int(pred) for pred in predictions[task]]
                results[f"true_{task}"] = encoder.inverse_transform(labels_for_inverse)
                results[f"pred_{task}"] = encoder.inverse_transform(
                    predictions_for_inverse
                )

            # If encoder is missing, log a warning and store raw labels/predictions
            else:
                logger.warning(
                    f"Encoder for task {task} not found. Skipping inverse transform."
                )
                results[f"true_{task}"] = labels[task]
                results[f"pred_{task}"] = predictions[task]

        #  Convert results to a DataFrame
        results_df = pd.DataFrame(results)

        # Add correctness columns for each task
        for task in self.output_tasks:
            results_df[f"{task}_correct"] = (
                results_df[f"true_{task}"] == results_df[f"pred_{task}"]
            )

        # If multiple tasks, add a column indicating if all tasks are correct
        if len(self.output_tasks) > 1:
            all_correct_col = pd.Series([True] * len(results_df))
            for task in self.output_tasks:
                all_correct_col &= results_df[f"{task}_correct"]
            results_df["all_correct"] = all_correct_col
        else:
            # For single task, all_correct is the same as the single task correctness
            results_df["all_correct"] = results_df[f"{self.output_tasks[0]}_correct"]

        # Create evaluation output directory, and save results
        os.makedirs(evaluation_output_dir, exist_ok=True)
        results_df.to_csv(
            os.path.join(evaluation_output_dir, "evaluation_report.csv"), index=False
        )

        logger.info("Evaluation report saved to evaluation_report.csv")

        # Comprehensive plotting
        self.plot_evaluation_results(results_df, evaluation_output_dir)

        return results_df

    def plot_evaluation_results(self, results_df, output_dir):
        """
        Generate comprehensive plots for the evaluation results.

        Args:
            results_df: DataFrame containing evaluation results
            output_dir: Directory for saving plot artifacts

        Side Effects:
            - Creates plots for per-task accuracy, confusion matrix, and
              sample predictions
            - Saves plots as image files in the specified directory
        """

        # Create output directory for plots
        plots_dir = os.path.join(output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)

        # Loop over each task to create individual plots
        for task in self.output_tasks:
            # Plot per-task accuracy
            plt.figure(figsize=(10, 6))
            correct_counts = results_df[f"{task}_correct"].value_counts(normalize=True)
            sns.barplot(x=["True", "False"], y=correct_counts)
            plt.title(f"{task.capitalize()} - Accuracy")
            plt.ylabel("Proportion")
            plt.savefig(os.path.join(plots_dir, f"{task}_accuracy.png"))
            plt.close()

            # Plot confusion matrix
            true_labels = results_df[f"true_{task}"]
            pred_labels = results_df[f"pred_{task}"]
            cm = confusion_matrix(true_labels, pred_labels)
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="coolwarm",
                xticklabels=["Class " + str(i) for i in range(cm.shape[1])],
                yticklabels=["Class " + str(i) for i in range(cm.shape[0])],
            )
            plt.title(f"{task.capitalize()} - Confusion Matrix")
            plt.xlabel("Predicted")
            plt.ylabel("True")
            plt.savefig(os.path.join(plots_dir, f"{task}_confusion_matrix.png"))
            plt.close()

            # Plot sample predictions
            sample_size = min(10, len(results_df))
            sample_df = results_df.sample(sample_size)
            plt.figure(figsize=(10, 6))
            sns.barplot(x="text", y="pred_" + task, data=sample_df)
            plt.title(f"{task.capitalize()} - Sample Predictions")
            plt.xticks(rotation=45, ha="right")
            plt.ylabel("Predicted Class")
            plt.savefig(os.path.join(plots_dir, f"{task}_sample_predictions.png"))
            plt.close()

        logger.info("Evaluation plots saved to: " + plots_dir)

    @staticmethod
    def calculate_metrics(preds, labels, task_name=""):
        """
        Compute comprehensive classification metrics for model evaluation.

        Calculates accuracy, F1-score, precision, and recall using weighted
        averaging to handle class imbalance. Generates detailed classification
        report with per-class statistics.

        Args:
            preds: Model predictions as numeric class indices
            labels: Ground truth labels as numeric class indices
            task_name: Descriptive name for logging context

        Returns:
            dict: Metrics dictionary containing:
                - acc: Accuracy score (0-1)
                - f1: Weighted F1-score (0-1)
                - prec: Weighted precision (0-1)
                - rec: Weighted recall (0-1)
                - report: Detailed classification report string

        Handles edge cases like empty datasets and length mismatches gracefully
        by returning zero metrics with appropriate warnings.
        """
        # Flatten preds and labels to ensure they are 1D arrays
        preds = np.array(preds).flatten()
        labels = np.array(labels).flatten()

        # If preds and labels have different lengths, return zero metrics
        if (len(preds) != len(labels)) or (len(labels) == 0):
            return {
                "acc": 0,
                "f1": 0,
                "prec": 0,
                "rec": 0,
                "report": "Length mismatch, or empty labels/preds",
            }

        # Get unique labels in the data
        unique_labels_in_data = np.unique(np.concatenate((labels, preds)))

        # Calculate metrics using classification report
        report_str = classification_report(
            labels,
            preds,
            zero_division=0,
            labels=unique_labels_in_data,
            target_names=[str(x) for x in unique_labels_in_data],
        )

        # Save the metrics in a dictionary
        metrics = {
            "acc": accuracy_score(labels, preds),
            "f1": f1_score(labels, preds, average="weighted", zero_division=0),
            "prec": precision_score(labels, preds, average="weighted", zero_division=0),
            "rec": recall_score(labels, preds, average="weighted", zero_division=0),
            "report": report_str,
        }

        return metrics

    @staticmethod
    def print_metrics(metrics_dict, split, loss=None):
        """
        Display formatted training metrics in a readable table format.

        Renders metrics for all tasks in a visually appealing table with
        color-coded headers and consistent decimal formatting. Supports
        different contexts (train/validation/test) with appropriate styling.

        Args:
            metrics_dict: Dict mapping task names to metric dictionaries
            split: Context string ('Train', 'Val', 'Test') for header styling
            loss: Optional loss value to display above metrics table

        Side Effects:
            - Prints colored headers and formatted tables to console
            - Uses tabulate library for professional table formatting
            - Applies context-appropriate terminal colors
        """

        # Define color mapping for different splits
        split_colors = {"Train": "cyan", "Val": "yellow", "Test": "green"}
        color = split_colors.get(split, "white")

        # Print header with color and bold attributes
        header = f" {split} Metrics "
        print(colored(f"\n{'='*20} {header} {'='*20}", color, attrs=["bold"]))

        # Print loss if provided
        if loss is not None:
            print(colored(f"Loss: {loss:.4f}", color))

        # Prepare table data with metrics for each task
        table_data = []
        headers = ["Task", "Accuracy", "F1 Score", "Precision", "Recall"]
        for task, metrics in metrics_dict.items():
            if isinstance(metrics, dict):
                table_data.append(
                    [
                        task.capitalize(),
                        f"{metrics.get('acc', 0):.4f}",
                        f"{metrics.get('f1', 0):.4f}",
                        f"{metrics.get('prec', 0):.4f}",
                        f"{metrics.get('rec', 0):.4f}",
                    ]
                )

        # Print table data
        if table_data:
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))

        # If no metrics available, print a warning message
        else:
            print(colored("No metrics to display for this split/task.", "red"))

        # Print footer with color
        print(colored(f"{'='* (40 + len(header))}", color))

    @staticmethod
    def promote_dynamic_to_baseline(weights_dir: str = "models/weights") -> bool:
        """
        Promote current dynamic model to baseline status for production use.

        Copies dynamic_weights.pt to baseline_weights.pt, effectively making
        the current best-performing model the new production baseline. This
        operation is typically performed after validating model performance
        meets promotion criteria.

        Args:
            weights_dir: Directory containing model weight files

        Returns:
            bool: True if promotion successful, False if dynamic model missing

        Side Effects:
            - Creates or overwrites baseline_weights.pt file
            - Logs promotion status and any errors encountered
        """

        # Define paths for dynamic and baseline weights
        dynamic_path = os.path.join(weights_dir, "dynamic_weights.pt")
        baseline_path = os.path.join(weights_dir, "baseline_weights.pt")

        # If dynamic weights exist, copy to baseline
        if os.path.exists(dynamic_path):
            shutil.copy(dynamic_path, baseline_path)
            logging.info(f"Promoted dynamic model to baseline: {baseline_path}")
            return True

        # If dynamic weights are missing, log an error
        else:
            logging.error(f"Dynamic weights not found at: {dynamic_path}")
            return False

    def should_promote_to_baseline(self, dynamic_f1, baseline_f1, threshold=0.01):
        """
        Determine whether dynamic model performance justifies baseline promotion.

        Compares dynamic model F1 score against current baseline with a
        configurable improvement threshold to prevent frequent updates from
        marginal improvements. Implements a simple but effective promotion
        strategy based on statistical significance.

        Args:
            dynamic_f1: F1 score of the newly trained dynamic model
            baseline_f1: F1 score of the current production baseline model
            threshold: Minimum improvement required for promotion (default: 0.01)

        Returns:
            bool: True if dynamic model should replace baseline, False otherwise

        Note:
            Uses emotion task F1 as the primary promotion criterion. In multi-task
            scenarios, consider weighted combinations of task performances.
        """

        # Check if dynamic F1 is significantly better than baseline F1
        return dynamic_f1 > baseline_f1 + threshold


class AzureMLManager:
    """
    Unified Azure ML manager for emotion classification pipeline.

    Handles all Azure ML operations including:
    - Model weight synchronization (download/upload)
    - Model promotion and versioning
    - Status reporting and configuration validation
    - Backup and recovery operations
    """

    def __init__(self, weights_dir="models/weights"):
        """
        Initialize Azure ML manager.

        Args:
            weights_dir: Directory path for local model weights storage
        """
        self.weights_dir = weights_dir
        self._azure_available = self._check_azure_availability()
        self._ml_client = None

        if self._azure_available:
            self._initialize_azure_client()

    def _check_azure_availability(self):
        """Check if Azure ML dependencies and credentials are available."""
        try:
            # Check required environment variables
            required_vars = [
                "AZURE_SUBSCRIPTION_ID",
                "AZURE_RESOURCE_GROUP",
                "AZURE_WORKSPACE_NAME",
            ]

            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            if missing_vars:
                logger.info(
                    "Azure ML not configured - missing env vars: " f"{missing_vars}"
                )
                return False

            # Try importing Azure ML dependencies
            import azure.ai.ml  # noqa: F401
            import azure.identity  # noqa: F401

            return True

        except ImportError as e:
            logger.info(f"Azure ML dependencies not available: {e}")
            return False
        except Exception as e:
            logger.warning(f"Azure ML availability check failed: {e}")
            return False

    def _initialize_azure_client(self):
        """Initialize Azure ML client with proper error handling."""
        try:
            from azure.ai.ml import MLClient
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self._ml_client = MLClient(
                credential=credential,
                subscription_id=os.environ.get("AZURE_SUBSCRIPTION_ID"),
                resource_group_name=os.environ.get("AZURE_RESOURCE_GROUP"),
                workspace_name=os.environ.get("AZURE_WORKSPACE_NAME"),
            )
            logger.info("Azure ML client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure ML client: {e}")
            self._azure_available = False

    def create_backup(self, timestamp=None):
        """
        Create timestamped backup of existing model weights.

        Args:
            timestamp: Optional timestamp string, defaults to current time
        """
        if timestamp is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_dir = os.path.join(self.weights_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        for model_file in ["baseline_weights.pt", "dynamic_weights.pt"]:
            model_path = os.path.join(self.weights_dir, model_file)
            if os.path.exists(model_path):
                backup_path = os.path.join(backup_dir, f"{model_file}.{timestamp}")
                import shutil

                shutil.copy2(model_path, backup_path)
                logger.info(f"Created backup: {backup_path}")

    def download_models(self, dry_run=False):
        """
        Download models from Azure ML if they don't exist locally.

        Args:
            dry_run: If True, only show what would be downloaded

        Returns:
            tuple: (baseline_downloaded, dynamic_downloaded)
        """
        baseline_path = os.path.join(self.weights_dir, "baseline_weights.pt")
        dynamic_path = os.path.join(self.weights_dir, "dynamic_weights.pt")

        baseline_downloaded = False
        dynamic_downloaded = False

        if dry_run:
            logger.info("DRY RUN - Would download:")
            if not os.path.exists(baseline_path):
                logger.info("  ✓ Baseline model from Azure ML")
                baseline_downloaded = True
            if not os.path.exists(dynamic_path):
                logger.info("  ✓ Dynamic model from Azure ML")
                dynamic_downloaded = True
            if os.path.exists(baseline_path) and os.path.exists(dynamic_path):
                logger.info("  (No downloads needed - all models exist locally)")
            return baseline_downloaded, dynamic_downloaded

        if not self._azure_available:
            logger.warning("Azure ML not available - cannot download models")
            return False, False

        os.makedirs(self.weights_dir, exist_ok=True)

        # Download baseline model if missing
        if not os.path.exists(baseline_path):
            baseline_downloaded = self._download_model(
                "emotion-clf-baseline", baseline_path
            )

        # Download dynamic model if missing
        if not os.path.exists(dynamic_path):
            dynamic_downloaded = self._download_model(
                "emotion-clf-dynamic", dynamic_path
            )

        return baseline_downloaded, dynamic_downloaded

    def _download_model(self, model_name, local_path):
        """Download a specific model from Azure ML."""
        try:
            model = self._ml_client.models.get(name=model_name, label="latest")
            self._ml_client.models.download(
                name=model_name,
                version=model.version,
                download_path=os.path.dirname(local_path),
            )
            logger.info(f"✓ {model_name} downloaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to download {model_name}: {e}")
            return False

    def upload_dynamic_model(self, f1_score, dry_run=False):
        """
        Upload dynamic model to Azure ML with F1 score metadata.

        Args:
            f1_score: F1 score to tag the model with
            dry_run: If True, only show what would be uploaded

        Returns:
            bool: True if upload successful, False otherwise
        """
        dynamic_path = os.path.join(self.weights_dir, "dynamic_weights.pt")

        if dry_run:
            msg = (
                "DRY RUN - Would upload dynamic model with F1 score: " f"{f1_score:.4f}"
            )
            logger.info(msg)
            return True

        if not self.validate_operation("upload", f1_score):
            return False

        if not self._azure_available:
            logger.warning("Azure ML not available - cannot upload model")
            return False

        try:
            from azure.ai.ml.constants import AssetTypes
            from azure.ai.ml.entities import Model as AzureModel

            # Create Azure ML model
            model = AzureModel(
                path=dynamic_path,
                type=AssetTypes.CUSTOM_MODEL,
                name="emotion-clf-dynamic",
                description=(
                    f"Dynamic emotion classification model " f"(F1: {f1_score:.4f})"
                ),
                tags={
                    "f1_score": str(f1_score),
                    "model_type": "dynamic",
                    "framework": "pytorch",
                    "architecture": "deberta",
                },
            )

            # Upload to Azure ML
            registered_model = self._ml_client.models.create_or_update(model)
            success_msg = (
                f"✓ Dynamic model uploaded successfully " f"(F1: {f1_score:.4f})"
            )
            logger.info(success_msg)
            logger.info(f"  Model version: {registered_model.version}")

            return True

        except Exception as e:
            logger.error(f"Failed to upload dynamic model: {e}")
            return False

    def _upload_baseline_to_azure(self, baseline_path):
        """Upload baseline model to Azure ML."""
        try:
            from azure.ai.ml.constants import AssetTypes
            from azure.ai.ml.entities import Model as AzureModel

            # Get F1 score from dynamic model metadata if available
            f1_score = self._get_model_f1_score("dynamic")

            model = AzureModel(
                path=baseline_path,
                type=AssetTypes.CUSTOM_MODEL,
                name="emotion-clf-baseline",
                description=(
                    f"Baseline emotion classification model " f"(F1: {f1_score:.4f})"
                ),
                tags={
                    "f1_score": str(f1_score),
                    "model_type": "baseline",
                    "framework": "pytorch",
                    "architecture": "deberta",
                    "promoted_from": "dynamic",
                },
            )

            registered_model = self._ml_client.models.create_or_update(model)
            version_info = f"version: {registered_model.version}"
            logger.info(f"✓ New baseline uploaded to Azure ML ({version_info})")

        except Exception as e:
            logger.warning(f"Failed to upload baseline to Azure ML: {e}")

    def get_status_info(self):
        """
        Get comprehensive status information.

        Returns:
            dict: Combined configuration and model status information
        """
        return {
            "configuration": self._get_configuration_status(),
            "models": self._get_model_info(),
        }

    def _get_configuration_status(self):
        """Get detailed Azure ML configuration status."""
        status = {
            "azure_available": self._azure_available,
            "connection_status": (
                "Connected" if self._azure_available else "Not configured"
            ),
            "environment_variables": {},
            "authentication": {
                "available_methods": [],
                "service_principal_configured": False,
                "azure_cli_available": False,
            },
        }

        # Check environment variables
        required_vars = [
            "AZURE_SUBSCRIPTION_ID",
            "AZURE_RESOURCE_GROUP",
            "AZURE_WORKSPACE_NAME",
        ]
        optional_vars = ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"]

        for var in required_vars:
            value = os.environ.get(var)
            status["environment_variables"][var] = "✓ Set" if value else "✗ Missing"

        for var in optional_vars:
            value = os.environ.get(var)
            msg = "✓ Set (optional)" if value else "✗ Not set (optional)"
            status["environment_variables"][var] = msg

        # Check authentication methods
        self._check_authentication_methods(status["authentication"])

        return status

    def _check_authentication_methods(self, auth_info):
        """Check available authentication methods."""
        # Check service principal configuration
        service_principal_vars = [
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
            "AZURE_TENANT_ID",
        ]
        if all(os.environ.get(var) for var in service_principal_vars):
            auth_info["service_principal_configured"] = True
            auth_info["available_methods"].append("Service Principal")

        # Check Azure CLI
        try:
            subprocess.run(["az", "--version"], capture_output=True, check=True)
            auth_info["azure_cli_available"] = True
            auth_info["available_methods"].append("Azure CLI")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        if not auth_info["available_methods"]:
            auth_info["available_methods"].append("Default credential chain")

    def _get_model_info(self):
        """Get comprehensive model information."""
        return {
            "azure_available": self._azure_available,
            "local": self._get_local_model_info(),
            "azure_ml": self._get_azure_model_info(),
        }

    def _get_local_model_info(self):
        """Get information about local model files."""
        baseline_path = os.path.join(self.weights_dir, "baseline_weights.pt")
        dynamic_path = os.path.join(self.weights_dir, "dynamic_weights.pt")

        info = {
            "baseline_exists": os.path.exists(baseline_path),
            "dynamic_exists": os.path.exists(dynamic_path),
        }

        for model_type, path in [
            ("baseline", baseline_path),
            ("dynamic", dynamic_path),
        ]:
            if info[f"{model_type}_exists"]:
                stat = os.stat(path)
                info[f"{model_type}_size"] = stat.st_size
                info[f"{model_type}_modified"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)
                )

        return info

    def _get_azure_model_info(self):
        """Get information about Azure ML models."""
        info = {}

        if not self._azure_available:
            return info

        for model_name in ["emotion-clf-baseline", "emotion-clf-dynamic"]:
            try:
                model = self._ml_client.models.get(name=model_name, label="latest")
                created_at = model.creation_context.created_at
                created_time = (
                    created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else None
                )
                info[model_name] = {
                    "version": model.version,
                    "created_time": created_time,
                    "tags": model.tags or {},
                }
            except Exception as e:
                logger.debug(f"Model {model_name} not found in Azure ML: {e}")
                info[model_name] = {"error": str(e)}

        return info

    def _get_model_f1_score(self, model_type):
        """Get F1 score for a model from Azure ML metadata."""
        if not self._azure_available:
            return 0.0

        model_name = f"emotion-clf-{model_type}"
        try:
            model = self._ml_client.models.get(name=model_name, label="latest")
            if model.tags and "f1_score" in model.tags:
                return float(model.tags["f1_score"])
        except Exception as e:
            logger.debug(f"Could not get F1 score for {model_name}: {e}")

        return 0.0

    def print_status_report(self, save_to_file=None):
        """
        Generate and display comprehensive status report.

        Args:
            save_to_file: Optional file path to save status as JSON
        """
        status_info = self.get_status_info()
        config_status = status_info["configuration"]
        model_info = status_info["models"]

        print("\n=== Azure ML Configuration Status ===")
        print(f"Connection Status: {config_status['connection_status']}")

        print("\n--- Environment Variables ---")
        for var, status in config_status["environment_variables"].items():
            print(f"{var}: {status}")

        print("\n--- Authentication Methods ---")
        auth_info = config_status["authentication"]
        methods = ", ".join(auth_info["available_methods"])
        print(f"Available methods: {methods}")

        sp_configured = auth_info["service_principal_configured"]
        cli_available = auth_info["azure_cli_available"]

        sp_status = "✓ Configured" if sp_configured else "✗ Not configured"
        cli_status = "✓ Available" if cli_available else "✗ Not installed"

        print(f"Service Principal: {sp_status}")
        print(f"Azure CLI: {cli_status}")

        if not config_status["azure_available"]:
            self._print_setup_instructions()

        print("\n=== Azure ML Model Sync Status ===")
        azure_status = "✓" if model_info["azure_available"] else "✗"
        print(f"Azure ML Available: {azure_status}")

        self._print_local_model_status(model_info["local"])

        if model_info["azure_available"]:
            self._print_azure_model_status(model_info["azure_ml"])

        # Save status to file if requested
        if save_to_file:
            os.makedirs(os.path.dirname(save_to_file), exist_ok=True)
            with open(save_to_file, "w") as f:
                json.dump(status_info, f, indent=2)
            print(f"\nModel sync status saved to: {save_to_file}")

    def _print_setup_instructions(self):
        """Print Azure ML setup instructions."""
        print("\n💡 To enable Azure ML sync:")
        cli_url = "https://docs.microsoft.com/en-us/cli/azure/" "install-azure-cli"
        print(f"1. Install Azure CLI: {cli_url}")
        print("2. Run 'az login' for interactive authentication")
        sp_vars = "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID"
        print(f"3. Or set {sp_vars} for service principal")
        print("4. Ensure you have access to the Azure ML workspace")

    def _print_local_model_status(self, local_info):
        """Print local model status information."""
        print("\n--- Local Models ---")
        baseline_status = "✓" if local_info["baseline_exists"] else "✗"
        dynamic_status = "✓" if local_info["dynamic_exists"] else "✗"

        print(f"Baseline weights: {baseline_status}")
        if local_info["baseline_exists"]:
            size_mb = local_info["baseline_size"] / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Modified: {local_info['baseline_modified']}")

        print(f"Dynamic weights: {dynamic_status}")
        if local_info["dynamic_exists"]:
            size_mb = local_info["dynamic_size"] / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Modified: {local_info['dynamic_modified']}")

    def _print_azure_model_status(self, azure_info):
        """Print Azure ML model status information."""
        print("\n--- Azure ML Models ---")

        for model_name in ["emotion-clf-baseline", "emotion-clf-dynamic"]:
            if model_name in azure_info:
                model_info = azure_info[model_name]
                if "version" in model_info:
                    print(f"{model_name}: v{model_info['version']}")
                    if model_info.get("created_time"):
                        print(f"  Created: {model_info['created_time']}")
                    if model_info.get("tags", {}).get("f1_score"):
                        print(f"  F1 Score: {model_info['tags']['f1_score']}")
                else:
                    print(f"{model_name}: not found")

    def sync_on_startup(self):
        """Perform automatic sync operations on startup."""
        return self.download_models()

    def handle_post_training_sync(
        self, f1_score, auto_upload=False, auto_promote_threshold=0.85
    ):
        """
        Handle sync operations after training completion.

        Args:
            f1_score: F1 score from training
            auto_upload: Whether to automatically upload dynamic model
            auto_promote_threshold: F1 threshold for auto-promotion

        Returns:
            dict: Results of sync operations
        """
        results = {"uploaded": False, "promoted": False, "baseline_f1": None}

        if auto_upload and self._azure_available:
            results["uploaded"] = self.upload_dynamic_model(f1_score)

        # Check if we should auto-promote
        if f1_score >= auto_promote_threshold:
            baseline_f1 = self._get_model_f1_score("baseline")
            results["baseline_f1"] = baseline_f1

            # Promote if significantly better than baseline
            if f1_score > baseline_f1 + 0.01:  # 1% improvement threshold
                results["promoted"] = self.promote_dynamic_to_baseline()
                if results["promoted"]:
                    logger.info(
                        f"Auto-promoted model (F1: {f1_score:.4f} > "
                        f"baseline: {baseline_f1:.4f})"
                    )

        return results

    def _prepare_upload_bundle(self, source_weights_filename: str) -> Optional[str]:
        """Prepares a directory bundle for uploading to Azure ML."""
        bundle_dir = os.path.join(self.weights_dir, "upload_bundle")
        if os.path.exists(bundle_dir):
            shutil.rmtree(bundle_dir)
        os.makedirs(bundle_dir)

        # Copy model config
        config_path = os.path.join(self.weights_dir, "model_config.json")
        if not os.path.exists(config_path):
            logger.error("model_config.json not found, cannot create bundle.")
            return None
        shutil.copy2(config_path, bundle_dir)

        # Copy weights, renaming them to what the scoring script expects
        source_weights_path = os.path.join(self.weights_dir, source_weights_filename)
        if not os.path.exists(source_weights_path):
            logger.error(f"{source_weights_filename} not found, cannot create bundle.")
            return None

        target_weights_path = os.path.join(bundle_dir, "baseline_weights.pt")
        shutil.copy2(source_weights_path, target_weights_path)

        logger.info(f"Upload bundle created at: {bundle_dir}")
        return bundle_dir

    def validate_operation(self, operation, f1_score=None):
        """
        Validate that the requested operation can be performed.

        Args:
            operation: Operation to validate ('upload', 'promote', etc.)
            f1_score: F1 score for upload operations

        Returns:
            bool: True if operation is valid, False otherwise
        """
        dynamic_path = os.path.join(self.weights_dir, "dynamic_weights.pt")

        if operation == "upload":
            if not os.path.exists(dynamic_path):
                logger.error("Dynamic weights not found - cannot upload")
                return False
            if f1_score is None:
                logger.error("F1 score is required for upload operation")
                return False
        elif operation == "promote":
            if not os.path.exists(dynamic_path):
                logger.error("Dynamic weights not found - cannot promote")
                return False

        return True

    def promote_dynamic_to_baseline(self, dry_run=False):
        """
        Promote dynamic model to baseline (locally and in Azure ML).

        Args:
            dry_run: If True, only show what would be promoted

        Returns:
            bool: True if promotion successful, False otherwise
        """
        if dry_run:
            logger.info("DRY RUN - Would promote dynamic model to baseline")
            logger.info("  ✓ Copy dynamic_weights.pt → baseline_weights.pt")
            if self._azure_available:
                logger.info("  ✓ Upload new baseline to Azure ML")
            return True

        if not self.validate_operation("promote"):
            return False

        try:
            # Copy dynamic to baseline locally
            dynamic_path = os.path.join(self.weights_dir, "dynamic_weights.pt")
            baseline_path = os.path.join(self.weights_dir, "baseline_weights.pt")

            import shutil

            shutil.copy2(dynamic_path, baseline_path)
            logger.info("✓ Dynamic model copied to baseline locally")

            # Upload new baseline to Azure ML if available
            if self._azure_available:
                self._upload_baseline_to_azure(baseline_path)

            logger.info("✓ Dynamic model promoted to baseline successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to promote dynamic model to baseline: {e}")
            return False


def parse_arguments():
    """
    Parse command line arguments for training configuration.

    Returns:
        argparse.Namespace: Parsed arguments containing training parameters
    """
    parser = argparse.ArgumentParser(
        description="Emotion Classification Training Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Model configuration
    parser.add_argument(
        "--model-name",
        type=str,
        default="microsoft/deberta-v3-xsmall",
        help="HuggingFace transformer model name to use for training",
    )

    # Training hyperparameters
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for training and evaluation",
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Learning rate for the AdamW optimizer",
    )

    parser.add_argument(
        "--weight-decay",
        type=float,
        default=0.01,
        help="Weight decay for the AdamW optimizer",
    )

    parser.add_argument(
        "--epochs", type=int, default=1, help="Number of training epochs"
    )

    parser.add_argument(
        "--dropout-prob",
        type=float,
        default=0.1,
        help="Dropout probability for the model.",
    )

    # Data paths (for Azure ML integration)
    parser.add_argument(
        "--train-data", type=str, help="Path to training data CSV file (for Azure ML)"
    )

    parser.add_argument(
        "--test-data", type=str, help="Path to test data CSV file (for Azure ML)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/weights",
        help="Output directory for trained model weights and metrics",
    )

    parser.add_argument(
        "--encoders-dir",
        type=str,
        default="models/encoders",
        help="Directory containing label encoders",
    )

    parser.add_argument(
        "--auto-promote-threshold",
        type=float,
        default=0.85,
        help="F1 score threshold to automatically promote dynamic model to baseline.",
    )

    parser.add_argument(
        "--hidden-dim",
        type=int,
        default=256,
        help="Dimension of the hidden layers in the classifier head.",
    )

    # Feature engineering arguments
    parser.add_argument(
        "--feature-config-file",
        type=str,
        default="config/feature_config.json",
        help="Path to the feature configuration JSON file",
    )

    return parser.parse_args()


def main():
    """Main function for training the model."""
    load_dotenv()
    args = parse_arguments()
    logger.info("=== Starting Emotion Classification Training Pipeline ===")
    logger.info("Training Configuration:")
    logger.info(f"  Model Name: {args.model_name}")
    logger.info(f"  Batch Size: {args.batch_size}")
    logger.info(f"  Learning Rate: {args.learning_rate}")

    # Configuration
    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
    ENCODERS_DIR = os.path.join(BASE_DIR, "models", "encoders")
    WEIGHTS_DIR = (
        args.output_dir
        if args.output_dir
        else os.path.join(BASE_DIR, "models", "weights")
    )
    RESULTS_DIR = os.path.join(BASE_DIR, "results", "evaluation")

    # Training parameters - using argparse values
    if args.train_data and os.path.isdir(args.train_data):
        TRAIN_CSV_PATH = os.path.join(args.train_data, "train.csv")
    else:
        TRAIN_CSV_PATH = (
            args.train_data if args.train_data else os.path.join(DATA_DIR, "train.csv")
        )

    if args.test_data and os.path.isdir(args.test_data):
        TEST_CSV_PATH = os.path.join(args.test_data, "test.csv")
    else:
        TEST_CSV_PATH = (
            args.test_data if args.test_data else os.path.join(DATA_DIR, "test.csv")
        )

    OUTPUT_TASKS = ["emotion", "sub_emotion", "intensity"]
    MAX_LENGTH = 256
    VALIDATION_SPLIT = 0.1
    MODEL_NAME = args.model_name
    BATCH_SIZE = args.batch_size
    LEARNING_RATE = args.learning_rate
    EPOCHS = args.epochs

    # Feature configuration
    FEATURE_CONFIG = {
        "pos": False,
        "textblob": False,
        "vader": False,
        "tfidf": True,
        "emolex": True,
    }

    # Create directories
    for directory in [ENCODERS_DIR, WEIGHTS_DIR, RESULTS_DIR]:
        os.makedirs(directory, exist_ok=True)

    # ====================================================================
    # AZURE ML SYNC OPERATIONS - Pre-Training Setup
    # ====================================================================
    logger.info("Initializing Azure ML sync operations...")
    try:
        # Initialize Azure ML Manager for startup operations
        azure_manager_startup = AzureMLManager(weights_dir=WEIGHTS_DIR)

        # Perform startup sync (download models if they don't exist locally)
        logger.info("Checking for existing models and performing startup sync...")
        startup_results = azure_manager_startup.sync_on_startup()
        baseline_downloaded, dynamic_downloaded = startup_results

        if baseline_downloaded:
            logger.info("✓ Baseline model downloaded from Azure ML")
        if dynamic_downloaded:
            logger.info("✓ Dynamic model downloaded from Azure ML")
        if not (baseline_downloaded or dynamic_downloaded):
            logger.info("Local model files exist, skipping download")

    except Exception as e:
        logger.warning(f"Azure ML startup sync failed: {str(e)}")
        logger.info("Continuing with training without Azure ML sync")

    # Check if data files exist
    if not os.path.exists(TRAIN_CSV_PATH):
        logger.error(f"Training data not found: {TRAIN_CSV_PATH}")
        logger.error("Please ensure train.csv exists in data/processed/")
        sys.exit(1)

    if not os.path.exists(TEST_CSV_PATH):
        logger.error(f"Test data not found: {TEST_CSV_PATH}")
        logger.error("Please ensure test.csv exists in data/processed/")
        sys.exit(1)

    # Load data
    logger.info("Loading processed training and test data...")
    train_df = pd.read_csv(TRAIN_CSV_PATH)
    test_df = pd.read_csv(TEST_CSV_PATH)

    logger.info(f"Loaded {len(train_df)} training samples")
    logger.info(f"Loaded {len(test_df)} test samples")

    # Verify required columns exist
    required_columns = ["text"] + OUTPUT_TASKS
    for col in required_columns:
        if col not in train_df.columns:
            logger.error(f"Required column '{col}' not found in training data")
            sys.exit(1)
        if col not in test_df.columns:
            logger.error(f"Required column '{col}' not found in test data")
            sys.exit(1)

    # Set up device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Initialize tokenizer
    logger.info(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Initialize data preparation
    logger.info("Initializing data preparation pipeline...")
    data_prep = DataPreparation(
        output_columns=OUTPUT_TASKS,
        tokenizer=tokenizer,
        max_length=MAX_LENGTH,
        batch_size=BATCH_SIZE,
        feature_config=FEATURE_CONFIG,
        encoders_save_dir=ENCODERS_DIR,
    )

    # Prepare data loaders
    logger.info("Preparing data loaders...")
    train_dataloader, val_dataloader, test_dataloader = data_prep.prepare_data(
        train_df=train_df, test_df=test_df, validation_split=VALIDATION_SPLIT
    )

    # Get feature dimensions and class information
    feature_dim = data_prep.feature_extractor.get_feature_dim()
    num_classes = data_prep.get_num_classes()

    logger.info(f"Feature dimension: {feature_dim}")
    logger.info(f"Number of classes: {num_classes}")

    # Compute class weights for balanced training
    class_weights_tensor = {}
    if "emotion" in OUTPUT_TASKS:
        emotion_labels = data_prep.label_encoders["emotion"].transform(
            train_df["emotion"]
        )
        class_weights_emotion = compute_class_weight(
            "balanced", classes=np.unique(emotion_labels), y=emotion_labels
        )
        class_weights_tensor["emotion"] = torch.tensor(
            class_weights_emotion, dtype=torch.float
        ).to(device)
        logger.info(f"Computed class weights for emotion: {class_weights_emotion}")

    # Load model
    model_loader = ModelLoader(model_name=args.model_name)
    model = model_loader.load_model(
        feature_dim=feature_dim,
        num_classes=num_classes,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout_prob,
    )
    # Log model architecture
    logger.info(f"Model architecture:\n{model}")

    # Initialize trainer
    logger.info("Initializing trainer...")
    trainer = CustomTrainer(
        model=model,
        train_dataloader=train_dataloader,
        val_dataloader=val_dataloader,
        test_dataloader=test_dataloader,
        device=device,
        test_set_df=data_prep.test_df_split,
        class_weights_tensor=class_weights_tensor,
        encoders_dir=ENCODERS_DIR,
        output_tasks=OUTPUT_TASKS,
        learning_rate=LEARNING_RATE,
        weight_decay=args.weight_decay,
        epochs=EPOCHS,
        feature_config=FEATURE_CONFIG,
    )

    # Start training
    logger.info("=" * 60)
    logger.info("STARTING TRAINING")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        # Train and evaluate model
        trainer.train_and_evaluate(
            trained_model_output_dir=WEIGHTS_DIR,
            metrics_output_file=os.path.join(RESULTS_DIR, "training_metrics.json"),
        )

        # After training, we will promote the newly trained model
        # (which is now the baseline)
        # to be the dynamic one for evaluation purposes before potential promotion.
        # This seems a bit counter-intuitive, but it aligns with the existing logic
        # of evaluating a 'dynamic' model.
        trainer.promote_dynamic_to_baseline(weights_dir=WEIGHTS_DIR)

        training_time = time.time() - start_time
        logger.info(
            f"Training completed in {str(timedelta(seconds=int(training_time)))}"
        )

        # Perform final evaluation
        logger.info("=" * 60)
        logger.info("PERFORMING FINAL EVALUATION")
        logger.info("=" * 60)

        dynamic_model_path = os.path.join(WEIGHTS_DIR, "dynamic_weights.pt")
        if os.path.exists(dynamic_model_path):
            eval_results = trainer.evaluate_final_model(
                model_path=dynamic_model_path, evaluation_output_dir=RESULTS_DIR
            )

            logger.info("Final evaluation completed successfully")
            logger.info(f"Evaluation results saved to: {RESULTS_DIR}")

            # Display key metrics
            if eval_results is not None and not eval_results.empty:
                emotion_accuracy = eval_results["emotion_correct"].mean()
                sub_emotion_accuracy = eval_results["sub_emotion_correct"].mean()
                intensity_accuracy = eval_results["intensity_correct"].mean()
                overall_accuracy = eval_results["all_correct"].mean()

                logger.info("=" * 60)
                logger.info("FINAL RESULTS SUMMARY")
                logger.info("=" * 60)
                logger.info(f"Emotion Accuracy:     {emotion_accuracy:.4f}")
                logger.info(f"Sub-emotion Accuracy: {sub_emotion_accuracy:.4f}")
                logger.info(f"Intensity Accuracy:   {intensity_accuracy:.4f}")
                logger.info(f"Overall Accuracy:     {overall_accuracy:.4f}")
                logger.info("=" * 60)
        else:
            logger.warning(f"Dynamic model weights not found at: {dynamic_model_path}")

    except Exception as e:
        logger.error(f"Training failed with error: {str(e)}")
        raise

    # Model registration (optional)
    logger.info("Training pipeline completed successfully!")
    logger.info(f"Model weights saved in: {WEIGHTS_DIR}")
    logger.info(f"Evaluation results saved in: {RESULTS_DIR}")

    # ====================================================================
    # AZURE ML SYNC OPERATIONS - Post-Training Integration
    # ====================================================================
    logger.info("=" * 60)
    logger.info("STARTING AZURE ML SYNC OPERATIONS")
    logger.info("=" * 60)

    try:
        # Initialize Azure ML Manager
        azure_manager = AzureMLManager(weights_dir=WEIGHTS_DIR)

        # Print comprehensive status report
        azure_manager.print_status_report(
            save_to_file=os.path.join(RESULTS_DIR, "azure_sync_status.json")
        )

        # Calculate final F1 score for model sync
        final_f1_score = 0.0
        if eval_results is not None and not eval_results.empty:
            # Use overall accuracy as proxy for F1 score if F1 not directly available
            final_f1_score = eval_results["all_correct"].mean()
            logger.info(f"Using overall accuracy as F1 score: {final_f1_score:.4f}")

        # Perform post-training sync operations
        logger.info("Executing post-training sync operations...")
        sync_results = azure_manager.handle_post_training_sync(
            f1_score=final_f1_score,
            auto_upload=True,  # Automatically upload dynamic model
            auto_promote_threshold=args.auto_promote_threshold,  # if F1 > threshold
        )

        # Report sync results
        if sync_results["uploaded"]:
            upload_msg = (
                f"✓ Dynamic model uploaded to Azure ML " f"(F1: {final_f1_score:.4f})"
            )
            logger.info(upload_msg)
        else:
            logger.info("✗ Dynamic model upload skipped or failed")

        if sync_results["promoted"]:
            baseline_f1 = sync_results.get("baseline_f1", 0.0)
            promote_msg = (
                f"✓ Model promoted to baseline "
                f"(improved from {baseline_f1:.4f} to "
                f"{final_f1_score:.4f})"
            )
            logger.info(promote_msg)
        else:
            logger.info("✗ Model promotion skipped (threshold not met or failed)")

        # Optional: Create backup of current weights
        logger.info("Creating backup of trained weights...")
        azure_manager.create_backup()

        logger.info("=" * 60)
        logger.info("AZURE ML SYNC OPERATIONS COMPLETED")
        logger.info("=" * 60)

    except Exception as e:
        logger.warning(f"Azure ML sync operations failed: {str(e)}")
        logger.warning(
            "Training completed successfully, but Azure sync " "encountered issues"
        )
        logger.info("You can manually sync models later using the CLI tools")

    # Cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    logger.info("=== Emotion Classification Training Pipeline Complete ===")


if __name__ == "__main__":
    main()
