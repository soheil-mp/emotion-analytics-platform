"""
Azure ML Model Synchronization Manager
Handles bidirectional sync between local weights and Azure ML Model Registry
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import torch
from azure.ai.ml import MLClient
from azure.ai.ml.constants import AssetTypes
from azure.ai.ml.entities import Model as AzureModel
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class AzureMLSync:
    """
    Manages synchronization between local model weights and Azure ML Model Registry.

    Features:
    - Download models from Azure ML if local weights don't exist
    - Upload new models to Azure ML with proper tags
    - Sync baseline/dynamic model designations
    - Handle offline scenarios gracefully
    - Validate model integrity after downloads
    """

    def __init__(self, weights_dir: str = "models/weights"):
        """
        Initialize Azure ML synchronization manager.

        Args:
            weights_dir: Directory containing model weight files
        """
        load_dotenv()

        self.weights_dir = Path(weights_dir)
        self.weights_dir.mkdir(parents=True, exist_ok=True)

        # Azure ML configuration
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.workspace_name = os.getenv("AZURE_WORKSPACE_NAME")

        # Model names in Azure ML
        self.baseline_model_name = "emotion-clf-baseline"
        self.dynamic_model_name = "emotion-clf-dynamic"

        # Check Azure ML availability
        self._azure_available = self._check_azure_availability()
        self._ml_client = None
        self._auth_method = None

    def _validate_downloaded_model(
        self, model_path: Path, min_size_mb: float = 10.0
    ) -> bool:
        """
        Validate that a downloaded model file is complete and loadable.

        Args:
            model_path: Path to the downloaded model file
            min_size_mb: Minimum expected file size in MB

        Returns:
            True if model is valid, False otherwise
        """
        try:
            # Check file exists and has reasonable size
            if not model_path.exists():
                logger.error(f"Model file does not exist: {model_path}")
                return False

            file_size_mb = model_path.stat().st_size / (1024 * 1024)
            if file_size_mb < min_size_mb:
                logger.error(
                    f"Model file too small ({file_size_mb:.1f} MB < "
                    f"{min_size_mb} MB): {model_path}"
                )
                return False

            # Try to load the model weights to verify integrity
            try:
                with open(model_path, "rb") as f:
                    # Load just the keys to verify valid PyTorch state dict
                    state_dict = torch.load(f, map_location="cpu", weights_only=False)

                # Verify it's a dictionary with expected structure
                if not isinstance(state_dict, dict):
                    logger.error(
                        f"Model file is not a valid state dictionary: " f"{model_path}"
                    )
                    return False

                # Check for expected keys (basic sanity check)
                expected_key_patterns = [
                    "deberta.",
                    "emotion_classifier.",
                    "feature_projection.",
                ]
                has_expected_keys = any(
                    any(key.startswith(pattern) for key in state_dict.keys())
                    for pattern in expected_key_patterns
                )

                if not has_expected_keys:
                    # Try alternate patterns (for models with bert. prefix)
                    alt_patterns = [
                        "bert.",
                        "emotion_classifier.",
                        "feature_projection.",
                    ]
                    has_expected_keys = any(
                        any(key.startswith(pattern) for key in state_dict.keys())
                        for pattern in alt_patterns
                    )

                if not has_expected_keys:
                    logger.warning(
                        f"Model file may have unexpected structure: " f"{model_path}"
                    )
                    # Log the actual keys for debugging
                    sample_keys = list(state_dict.keys())[:5]
                    logger.warning(f"Sample keys: {sample_keys}")

                logger.info(
                    f"✅ Model validation successful: {model_path} "
                    f"({file_size_mb:.1f} MB)"
                )
                return True

            except Exception as e:
                logger.error(f"Failed to load model weights from {model_path}: {e}")
                return False

        except Exception as e:
            logger.error(f"Error validating model file {model_path}: {e}")
            return False

    def _get_ml_client(self) -> Optional[MLClient]:
        """
        Get Azure ML client with proper authentication.

        Returns:
            MLClient instance if successful, None if failed
        """
        if self._ml_client is not None:
            return self._ml_client

        if not self._azure_available:
            logger.debug("Azure ML not available, skipping client creation")
            return None

        try:
            # Try service principal authentication first
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant_id = os.getenv("AZURE_TENANT_ID")

            if client_id and client_secret and tenant_id:
                from azure.identity import ClientSecretCredential

                credential = ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                self._auth_method = "service_principal"
                logger.debug("Using service principal authentication")
            else:
                # Fall back to default credential chain
                credential = DefaultAzureCredential()
                self._auth_method = "default_credential"
                logger.debug("Using default credential chain")

            self._ml_client = MLClient(
                credential=credential,
                subscription_id=self.subscription_id,
                resource_group_name=self.resource_group,
                workspace_name=self.workspace_name,
            )

            # Test the connection
            _ = self._ml_client.workspaces.get(self.workspace_name)
            logger.info(
                f"Azure ML connection established successfully "
                f"using {self._auth_method}"
            )
            return self._ml_client

        except Exception as e:
            logger.warning(f"Failed to create Azure ML client: {e}")
            self._ml_client = None
            self._auth_method = None
            return None

    def _calculate_model_hash(self, model_path: Path) -> str:
        """
        Calculate hash of a model file for integrity verification.
        This is an alias for _calculate_file_hash for better readability.

        Args:
            model_path: Path to the model file

        Returns:
            SHA256 hash of the file
        """
        return self._calculate_file_hash(model_path)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file for integrity verification."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate hash for {file_path}: {e}")
            return ""

    def _create_model_backup(self, model_path: Path) -> Optional[Path]:
        """
        Create a backup of an existing model file before replacement.

        Args:
            model_path: Path to the model file to backup

        Returns:
            Path to the backup file, or None if backup failed
        """
        try:
            if not model_path.exists():
                logger.warning(f"Cannot backup non-existent file: {model_path}")
                return None

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{model_path.stem}_backup_{timestamp}{model_path.suffix}"
            backup_path = model_path.parent / backup_name

            # Copy file to backup location
            shutil.copy2(model_path, backup_path)

            # Verify backup was created successfully
            if backup_path.exists() and backup_path.stat().st_size > 0:
                logger.info(f"📋 Created model backup: {backup_path.name}")
                return backup_path
            else:
                logger.error(f"Failed to create backup: {backup_path}")
                return None

        except Exception as e:
            logger.error(f"Error creating model backup: {e}")
            return None

    def _restore_model_backup(self, model_path: Path, backup_path: Path) -> bool:
        """
        Restore a model from its backup file.

        Args:
            model_path: Path where the model should be restored
            backup_path: Path to the backup file

        Returns:
            True if restore was successful, False otherwise
        """
        try:
            if not backup_path or not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Remove corrupted/failed model if it exists
            if model_path.exists():
                model_path.unlink()

            # Copy backup to original location
            shutil.copy2(backup_path, model_path)

            # Verify restoration
            if model_path.exists() and model_path.stat().st_size > 0:
                logger.info(f"🔄 Restored model from backup: {backup_path.name}")

                # Clean up backup file after successful restore
                try:
                    backup_path.unlink()
                    logger.debug(f"Cleaned up backup file: {backup_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up backup: {cleanup_error}")

                return True
            else:
                logger.error("Failed to restore model from backup")
                return False

        except Exception as e:
            logger.error(f"Error restoring model backup: {e}")
            return False

    def _update_local_sync_status(self) -> None:
        """Update local sync status file with current file information."""
        try:
            sync_status_path = self.weights_dir / "sync_status.json"

            # Check current file status
            baseline_path = self.weights_dir / "baseline_weights.pt"
            dynamic_path = self.weights_dir / "dynamic_weights.pt"

            status_data = {
                "local": {
                    "baseline_exists": baseline_path.exists(),
                    "dynamic_exists": dynamic_path.exists(),
                    "last_sync": datetime.now().isoformat(),
                }
            }

            if baseline_path.exists():
                status_data["local"]["baseline_size"] = baseline_path.stat().st_size
                status_data["local"]["baseline_modified"] = datetime.fromtimestamp(
                    baseline_path.stat().st_mtime
                ).isoformat()
                status_data["local"]["baseline_hash"] = self._calculate_file_hash(
                    baseline_path
                )

            if dynamic_path.exists():
                status_data["local"]["dynamic_size"] = dynamic_path.stat().st_size
                status_data["local"]["dynamic_modified"] = datetime.fromtimestamp(
                    dynamic_path.stat().st_mtime
                ).isoformat()
                status_data["local"]["dynamic_hash"] = self._calculate_file_hash(
                    dynamic_path
                )

            # Preserve existing data if available
            if sync_status_path.exists():
                with open(sync_status_path, "r") as f:
                    existing_data = json.load(f)
                    # Merge with existing data, prioritizing new local data
                    existing_data.update(status_data)
                    status_data = existing_data

            # Write updated status
            with open(sync_status_path, "w") as f:
                json.dump(status_data, f, indent=2)

            logger.debug(f"Updated sync status: {sync_status_path}")

        except Exception as e:
            logger.warning(f"Could not update sync status: {e}")

            # Write updated status
            with open(sync_status_path, "w") as f:
                json.dump(status_data, f, indent=2)

            logger.debug(f"Updated sync status: {status_data['local']}")

        except Exception as e:
            logger.warning(f"Failed to update sync status: {e}")

    def _check_azure_availability(self) -> bool:
        """Check if Azure ML is available and configured with retry logic."""
        try:
            # Check required environment variables
            missing_vars = []
            if not self.subscription_id:
                missing_vars.append("AZURE_SUBSCRIPTION_ID")
            if not self.resource_group:
                missing_vars.append("AZURE_RESOURCE_GROUP")
            if not self.workspace_name:
                missing_vars.append("AZURE_WORKSPACE_NAME")

            if missing_vars:
                logger.warning(
                    f"Azure ML credentials incomplete. Missing: \
                        {', '.join(missing_vars)}"
                )
                logger.info(
                    "Operating in local-only mode. Set environment \
                    variables for Azure ML sync."
                )
                return False

            # Try multiple authentication methods in order of preference
            credential = None
            auth_method = "unknown"

            # Method 1: Service Principal (if client_id and client_secret are set)
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant_id = os.getenv("AZURE_TENANT_ID")

            if client_id and client_secret and tenant_id:
                from azure.identity import ClientSecretCredential

                credential = ClientSecretCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                auth_method = "service_principal"
            else:
                # Method 2: Try Azure CLI credentials first (most
                # reliable when az login was used)
                try:
                    from azure.identity import AzureCliCredential

                    credential = AzureCliCredential()
                    auth_method = "azure_cli"
                except Exception as cli_error:
                    logger.debug(f"Azure CLI credential failed: {cli_error}")

                    # Method 3: Fall back to default credential chain
                    credential = DefaultAzureCredential()
                    auth_method = "default_credential"
            self._ml_client = MLClient(
                credential=credential,
                subscription_id=self.subscription_id,
                resource_group_name=self.resource_group,
                workspace_name=self.workspace_name,
            )

            # Store auth method and test connection with retry logic
            self._auth_method = auth_method
            return self._test_azure_connection_with_retry(auth_method)

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Azure ML not available: {error_msg}")

            # Provide specific guidance based on the error
            if (
                "client_id should be the id of a Microsoft Entra application"
                in error_msg
            ):
                logger.info(
                    "💡 Authentication failed. \
                    Try one of these options:"
                )
                logger.info(
                    "   1. Run 'az login' in your terminal for \
                    interactive authentication"
                )
                logger.info(
                    "   2. Set AZURE_CLIENT_ID and AZURE_CLIENT_SECRET \
                    for service principal auth"
                )
                logger.info(
                    "   3. Use managed identity if running on Azure \
                    infrastructure"
                )
            elif "AADSTS" in error_msg:
                logger.info(
                    "💡 Azure Active Directory authentication issue. \
                    Try 'az login' or check your credentials."
                )
            else:
                logger.info("💡 Check your Azure credentials and network connection.")
            return False

    def _test_azure_connection_with_retry(
        self, auth_method: str, max_retries: int = 2
    ) -> bool:
        """Test Azure ML connection with retry logic for network issues."""
        for attempt in range(max_retries + 1):
            try:
                # Test connection
                self._ml_client.workspaces.get(self.workspace_name)
                logger.info(
                    f"Azure ML connection established successfully \
                    using {auth_method}"
                )
                return True

            except (ConnectionResetError, HttpResponseError) as e:
                if (
                    "Connection aborted" in str(e)
                    or "Connection broken" in str(e)
                    or "reset" in str(e).lower()
                ):
                    if attempt < max_retries:
                        wait_time = (attempt + 1) * 2  # 2, 4 seconds
                        logger.warning(
                            f"Connection test failed (attempt \
                            {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        logger.info(
                            f"Retrying connection test in {wait_time} \
                            seconds..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning(
                            f"Azure ML connection failed after \
                            {max_retries + 1} attempts due to network issues"
                        )
                        logger.info(
                            "💡 Network connectivity issues detected. \
                            Operations may fail."
                        )
                        logger.info("   • Check your internet connection")
                        logger.info("   • Try again in a few moments")
                        return False
                else:
                    logger.warning(f"Azure ML connection failed: {e}")
                    return False

            except Exception as e:
                logger.warning(f"Azure ML connection failed: {e}")
                return False

        return False

    def _ensure_azure_connection(self) -> bool:
        """Ensure Azure ML connection is available, re-establishing if needed."""
        if not self._azure_available:
            return False

        # Test if connection is still valid
        try:
            self._ml_client.workspaces.get(self.workspace_name)
            return True
        except Exception:
            logger.info("Azure ML connection lost, attempting to reconnect...")
            self._azure_available = self._check_azure_availability()
            return self._azure_available

    def sync_on_startup(self) -> Tuple[bool, bool]:
        """
        Sync models on startup - download from Azure ML if local files don't exist.

        Returns:
            Tuple of (baseline_synced, dynamic_synced)
        """
        baseline_synced = False
        dynamic_synced = False

        if not self._azure_available:
            logger.info("Azure ML not available, using local weights only")
            return baseline_synced, dynamic_synced

        # Check and sync baseline model
        baseline_path = self.weights_dir / "baseline_weights.pt"
        if not baseline_path.exists():
            logger.info(
                "Baseline weights not found locally, \
                downloading from Azure ML..."
            )
            baseline_synced = self._download_model_from_azure(
                self.baseline_model_name, baseline_path
            )

        # Check and sync dynamic model
        dynamic_path = self.weights_dir / "dynamic_weights.pt"
        if not dynamic_path.exists():
            logger.info(
                "Dynamic weights not found locally, downloading \
                from Azure ML..."
            )
            dynamic_synced = self._download_model_from_azure(
                self.dynamic_model_name, dynamic_path
            )

        return baseline_synced, dynamic_synced

    def _download_model_from_azure(self, model_name: str, local_path: Path) -> bool:
        """
        Download a model from Azure ML to local path with backup and validation.

        Args:
            model_name: Name of the model in Azure ML
            local_path: Local path where model should be saved

        Returns:
            True if download and validation successful
        """
        try:
            # Check if Azure ML client is properly initialized
            if self._ml_client is None:
                logger.error(
                    "Azure ML client is not initialized. Cannot download model."
                )
                return False

            # Create backup of existing model if it exists
            backup_path = None
            if local_path.exists():
                backup_path = self._create_model_backup(local_path)
                # Calculate hash of current model for comparison
                original_hash = self._calculate_model_hash(local_path)
                logger.info(f"📊 Current model hash: {original_hash[:16]}...")

            # Get latest version of the model
            try:
                model = self._ml_client.models.get(model_name, label="latest")
                logger.info(
                    f"🔄 Downloading {model_name} v{model.version} " f"from Azure ML..."
                )
            except Exception as model_error:
                logger.error(
                    f"Model '{model_name}' not found in Azure ML "
                    f"workspace: {model_error}"
                )
                return False

            # Download model to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                downloaded_path = self._ml_client.models.download(
                    name=model_name, version=model.version, download_path=temp_dir
                )

                # Handle case where download path might be None or the temp_dir itself
                search_path = (
                    Path(downloaded_path) if downloaded_path else Path(temp_dir)
                )

                # Find the .pt file in downloaded content
                pt_files = list(search_path.rglob("*.pt"))
                if pt_files:
                    # Copy to temporary location first
                    temp_model_path = local_path.with_suffix(".tmp")
                    shutil.copy2(pt_files[0], temp_model_path)

                    # Validate the downloaded model file
                    if self._validate_downloaded_model(temp_model_path):
                        # Calculate hash of new model
                        new_hash = self._calculate_model_hash(temp_model_path)

                        # Move validated model to final location
                        if temp_model_path.exists():
                            shutil.move(str(temp_model_path), str(local_path))

                        file_size_mb = local_path.stat().st_size / (1024 * 1024)
                        logger.info(
                            f"✅ Successfully downloaded {model_name} v{model.version} "
                            f"({file_size_mb:.1f} MB)"
                        )
                        logger.info(f"📊 New model hash: {new_hash[:16]}...")

                        # Check if model actually changed
                        if backup_path and original_hash == new_hash:
                            logger.warning(
                                "⚠️  Downloaded model has same hash as existing "
                                "model - no actual update occurred"
                            )

                        return True
                    else:
                        logger.error(
                            f"❌ Downloaded model failed validation: {model_name}"
                        )
                        # Clean up temporary file
                        if temp_model_path.exists():
                            temp_model_path.unlink()

                        # Restore backup if available
                        if backup_path and local_path.exists():
                            logger.info("🔄 Restoring original model from backup...")
                            self._restore_model_backup(local_path, backup_path)

                        return False
                else:
                    logger.error(f"No .pt file found in downloaded model {model_name}")
                    logger.info(f"Available files: {list(search_path.rglob('*'))}")
                    return False

        except Exception as e:
            logger.error(f"Failed to download {model_name} from Azure ML: {e}")

            # Restore backup if available and original was removed
            if backup_path and not local_path.exists():
                logger.info("🔄 Restoring original model from backup due to error...")
                self._restore_model_backup(local_path, backup_path)

            return False

    def upload_dynamic_model(
        self, f1_score: float, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Upload dynamic model to Azure ML with retry logic for reliability.

        Args:
            f1_score: F1 score of the model
            metadata: Additional metadata to store with the model

        Returns:
            True if upload successful
        """
        if not self._azure_available:
            logger.warning("Azure ML not available, skipping model upload")
            return False

        dynamic_path = self.weights_dir / "dynamic_weights.pt"
        if not dynamic_path.exists():
            logger.error("Dynamic weights file not found, cannot upload")
            return False

        # Check file size and log
        file_size_mb = dynamic_path.stat().st_size / (1024 * 1024)
        logger.info(f"Uploading dynamic model ({file_size_mb:.1f} MB) to Azure ML...")

        return self._upload_model_with_retry(
            model_path=dynamic_path,
            model_name=self.dynamic_model_name,
            model_type="dynamic",
            f1_score=f1_score,
            metadata=metadata,
            max_retries=3,
        )

    def _upload_model_with_retry(
        self,
        model_path: Path,
        model_name: str,
        model_type: str,
        f1_score: float,
        metadata: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> bool:
        """
        Upload model with retry logic and exponential backoff.

        Args:
            model_path: Path to the model file
            model_name: Name for the model in Azure ML
            model_type: Type of model (baseline/dynamic)
            f1_score: F1 score of the model
            metadata: Additional metadata
            max_retries: Maximum number of retry attempts

        Returns:
            True if upload successful
        """
        for attempt in range(max_retries + 1):
            try:
                # Prepare model metadata
                model_metadata = {
                    "model_type": model_type,
                    "f1_score": str(f1_score),
                    "upload_time": datetime.now().isoformat(),
                    "framework": "pytorch",
                    "upload_attempt": str(attempt + 1),
                    "file_size_mb": str(
                        round(model_path.stat().st_size / (1024 * 1024), 2)
                    ),
                }

                if metadata:
                    model_metadata.update(metadata)

                # Create temporary directory with complete model package
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_model_dir = Path(temp_dir) / "model"
                    temp_model_dir.mkdir()

                    # Copy model weights file
                    temp_model_file = temp_model_dir / f"{model_type}_weights.pt"
                    shutil.copy2(model_path, temp_model_file)

                    # Copy model configuration file (required by scoring script)
                    config_source = Path(self.weights_dir) / "model_config.json"
                    config_target = temp_model_dir / "model_config.json"
                    if config_source.exists():
                        shutil.copy2(config_source, config_target)
                        logger.info("✅ Included model_config.json in package")
                    else:
                        # Create a basic config if it doesn't exist
                        logger.warning(
                            f"⚠ model_config.json not found at {config_source},"
                            " creating default"
                        )
                        default_config = {
                            "model_name": "microsoft/deberta-v3-xsmall",
                            "feature_dim": 121,
                            "num_classes": {
                                "emotion": 7,
                                "sub_emotion": 28,
                                "intensity": 3,
                            },
                            "hidden_dim": 512,
                            "dropout": 0.3,
                            "output_tasks": ["emotion", "sub_emotion", "intensity"],
                            "feature_config": {
                                "pos": False,
                                "textblob": False,
                                "vader": False,
                                "tfidf": True,
                                "emolex": True,
                            },
                        }
                        with open(config_target, "w") as f:
                            json.dump(default_config, f, indent=2)
                        logger.info("✅ Created default model_config.json")

                    # Copy encoders directory if it exists
                    encoders_source = Path("models/encoders")
                    if encoders_source.exists():
                        encoders_target = temp_model_dir / "encoders"
                        encoders_target.mkdir(exist_ok=True)
                        for encoder_file in encoders_source.glob("*.pkl"):
                            shutil.copy2(
                                encoder_file, encoders_target / encoder_file.name
                            )
                            logger.info(f"✅ Included encoder: {encoder_file.name}")

                    # Copy feature extraction files if they exist
                    feature_files = ["NRC-Emotion-Lexicon-Wordlevel-v0.92.txt"]

                    features_target = temp_model_dir / "features"
                    features_target.mkdir(exist_ok=True)

                    for feature_file in feature_files:
                        # Check in multiple locations
                        source_paths = [
                            Path(self.weights_dir) / feature_file,
                            Path("models/features/EmoLex") / feature_file,
                            Path("models/features") / feature_file,
                        ]

                        for source_path in source_paths:
                            if source_path.exists():
                                target_path = features_target / feature_file
                                shutil.copy2(source_path, target_path)
                                logger.info(f"✅ Included {feature_file} in package")
                                break

                    # Create comprehensive model metadata file
                    with open(temp_model_dir / "metadata.json", "w") as f:
                        json.dump(model_metadata, f, indent=2)

                    # Create Azure ML model
                    azure_model = AzureModel(
                        path=str(temp_model_dir),
                        name=model_name,
                        description=f"{model_type.title()} emotion \
                            classification model (F1: {f1_score:.4f})",
                        type=AssetTypes.CUSTOM_MODEL,
                        tags=model_metadata,
                    )

                    # Upload to Azure ML with timeout handling
                    logger.info(
                        f"Attempting upload (attempt {attempt + 1}\
                        /{max_retries + 1})..."
                    )
                    registered_model = self._ml_client.models.create_or_update(
                        azure_model
                    )

                    logger.info(
                        f"✅ Successfully uploaded {model_type} \
                        model v{registered_model.version} to Azure ML"
                    )
                    return True

            except (ConnectionResetError, HttpResponseError) as e:
                if (
                    "Connection aborted" in str(e)
                    or "Connection broken" in str(e)
                    or "reset" in str(e).lower()
                ):
                    if attempt < max_retries:
                        # Exponential backoff: 2, 5, 9 seconds
                        wait_time = (2**attempt) + 1
                        logger.warning(
                            f"Upload failed due to connection \
                            issue (attempt {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(
                            f"Upload failed after {max_retries + 1} \
                            attempts due to connection issues: {e}"
                        )
                        logger.info("💡 Large file upload tips:")
                        logger.info("   • Check your internet connection stability")
                        logger.info("   • Try again during off-peak hours")
                        logger.info("   • Consider splitting large models if possible")
                        return False
                else:
                    logger.error(f"Upload failed with HTTP error: {e}")
                    return False

            except Exception as e:
                logger.error(f"Upload failed with unexpected error: {e}")
                if attempt < max_retries:
                    wait_time = (2**attempt) + 1
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Upload failed after {max_retries + 1} attempts")
                    return False

        return False

    def promote_dynamic_to_baseline(self) -> bool:
        """
        Promote the current dynamic model to become the new baseline in Azure ML.

        Returns:
            True if promotion successful
        """
        if not self._azure_available:
            logger.warning("Azure ML not available, performing local promotion only")
            return self._promote_local_only()

        # Test and re-establish Azure connection if needed
        if not self._test_azure_connection_with_retry(self._auth_method):
            logger.warning(
                "Azure ML connection failed, performing local \
                promotion only"
            )
            return self._promote_local_only()

        try:
            # Check if dynamic model exists in Azure ML with retry
            dynamic_model = None
            for attempt in range(3):
                try:
                    dynamic_model = self._ml_client.models.get(
                        self.dynamic_model_name, label="latest"
                    )
                    break
                except ResourceNotFoundError:
                    logger.warning(
                        f"No dynamic model found in Azure ML \
                        ({self.dynamic_model_name})"
                    )
                    logger.info(
                        "💡 Upload a dynamic model first before \
                        promoting to baseline"
                    )
                    logger.info(
                        "    You can upload by running: poetry run \
                        emotion-clf upload-model"
                    )
                    # Still do local promotion
                    return self._promote_local_only()
                except (ConnectionResetError, HttpResponseError) as e:
                    if attempt < 2:
                        wait_time = 2**attempt
                        logger.warning(
                            f"Connection error getting dynamic \
                            model (attempt {attempt + 1}/3): {e}"
                        )
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        # Re-establish connection
                        self._ensure_azure_connection()
                    else:
                        logger.error(
                            f"Failed to get dynamic model after 3 \
                            attempts: {e}"
                        )
                        logger.info("Falling back to local-only promotion...")
                        return self._promote_local_only()

            if not dynamic_model:
                logger.error("Could not retrieve dynamic model from Azure ML")
                return self._promote_local_only()

            logger.info(
                f"Promoting dynamic model v{dynamic_model.version} \
                to baseline..."
            )

            # Extract F1 score from metadata if available
            f1_score = 0.0
            if dynamic_model.tags and "f1_score" in dynamic_model.tags:
                try:
                    f1_score = float(dynamic_model.tags["f1_score"])
                except (ValueError, TypeError):
                    pass

            # Prepare metadata for baseline
            baseline_metadata = dynamic_model.tags.copy() if dynamic_model.tags else {}
            baseline_metadata["model_type"] = "baseline"
            baseline_metadata["promoted_from_dynamic"] = dynamic_model.version
            baseline_metadata["promotion_time"] = datetime.now().isoformat()

            # Use local dynamic weights file directly for upload
            # (more reliable than downloading)
            dynamic_path = self.weights_dir / "dynamic_weights.pt"
            if not dynamic_path.exists():
                logger.error("Local dynamic weights not found for promotion")
                return self._promote_local_only()

            logger.info("Uploading promoted model as new baseline...")

            # Use the reliable upload method for baseline
            upload_success = self._upload_model_with_retry(
                model_path=dynamic_path,
                model_name=self.baseline_model_name,
                model_type="baseline",
                f1_score=f1_score,
                metadata=baseline_metadata,
                max_retries=3,
            )

            if upload_success:
                # Update local files
                self._promote_local_only()
                logger.info("✅ Successfully promoted dynamic to baseline in Azure ML")
                return True
            else:
                logger.error("Failed to upload promoted baseline model")
                logger.info("Performing local promotion only...")
                return self._promote_local_only()

        except Exception as e:
            logger.error(f"Failed to promote model in Azure ML: {e}")
            logger.info("Falling back to local-only promotion...")
            return self._promote_local_only()

    def _promote_local_only(self) -> bool:
        """Promote dynamic to baseline locally only."""
        try:
            dynamic_path = self.weights_dir / "dynamic_weights.pt"
            baseline_path = self.weights_dir / "baseline_weights.pt"

            if dynamic_path.exists():
                shutil.copy2(dynamic_path, baseline_path)
                logger.info("Local promotion: dynamic → baseline completed")
                return True
            else:
                logger.error("Dynamic weights not found for local promotion")
                return False
        except Exception as e:
            logger.error(f"Local promotion failed: {e}")
            return False

    def get_model_info(self) -> Dict:
        """Get information about both local and Azure ML models."""
        info = {"local": {}, "azure_ml": {}, "azure_available": self._azure_available}

        # Local model info
        baseline_path = self.weights_dir / "baseline_weights.pt"
        dynamic_path = self.weights_dir / "dynamic_weights.pt"

        info["local"]["baseline_exists"] = baseline_path.exists()
        info["local"]["dynamic_exists"] = dynamic_path.exists()

        if baseline_path.exists():
            info["local"]["baseline_size"] = baseline_path.stat().st_size
            info["local"]["baseline_modified"] = datetime.fromtimestamp(
                baseline_path.stat().st_mtime
            ).isoformat()

        if dynamic_path.exists():
            info["local"]["dynamic_size"] = dynamic_path.stat().st_size
            info["local"]["dynamic_modified"] = datetime.fromtimestamp(
                dynamic_path.stat().st_mtime
            ).isoformat()

        # Azure ML model info
        if self._azure_available:
            try:
                for model_name in [self.baseline_model_name, self.dynamic_model_name]:
                    try:
                        model = self._ml_client.models.get(model_name, label="latest")
                        created_time = None
                        if model.creation_context:
                            created_time = model.creation_context.created_at.isoformat()
                        info["azure_ml"][model_name] = {
                            "version": model.version,
                            "created_time": created_time,
                            "tags": model.tags,
                        }
                    except Exception:
                        info["azure_ml"][model_name] = {"status": "not_found"}
            except Exception as e:
                info["azure_ml"]["error"] = str(e)

        return info

    def get_configuration_status(self) -> Dict:
        """
        Get detailed Azure ML configuration status for troubleshooting.

        Returns:
            Dictionary with configuration details and status
        """
        # Check authentication methods available
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")

        auth_methods = []
        if client_id and client_secret and tenant_id:
            auth_methods.append("Service Principal")
        if shutil.which("az"):  # Check if Azure CLI is installed
            auth_methods.append("Azure CLI")
        auth_methods.append("Default Credential Chain")

        # Checkings
        azure_subscription_id = "✓ Set" if self.subscription_id else "✗ Missing"
        azure_resource_group = "✓ Set" if self.resource_group else "✗ Missing"
        azure_workspace_name = "✓ Set" if self.workspace_name else "✗ Missing"
        azure_client_id = "✓ Set" if client_id else "✗ Not set (optional)"
        azure_client_secret = "✓ Set" if client_secret else "✗ Not set (optional)"
        azure_tenant_id = "✓ Set" if tenant_id else "✗ Not set (optional)"
        connection_status = "Connected" if self._azure_available else "Not connected"
        subscription_id_status = (
            self.subscription_id[:8] + "..."
            if self.subscription_id
            else "Not configured"
        )

        return {
            "environment_variables": {
                "AZURE_SUBSCRIPTION_ID": azure_subscription_id,
                "AZURE_RESOURCE_GROUP": azure_resource_group,
                "AZURE_WORKSPACE_NAME": azure_workspace_name,
                "AZURE_CLIENT_ID": azure_client_id,
                "AZURE_CLIENT_SECRET": azure_client_secret,
                "AZURE_TENANT_ID": azure_tenant_id,
            },
            "authentication": {
                "available_methods": auth_methods,
                "service_principal_configured": bool(
                    client_id and client_secret and tenant_id
                ),
                "azure_cli_available": bool(shutil.which("az")),
            },
            "azure_available": self._azure_available,
            "connection_status": connection_status,
            "workspace_name": self.workspace_name or "Not configured",
            "resource_group": self.resource_group or "Not configured",
            "subscription_id": subscription_id_status,
        }

    def auto_sync_on_startup(self, check_for_updates=True) -> Dict[str, bool]:
        """
        Comprehensive auto-sync on startup - downloads missing models and checks
        for updates.

        Args:
            check_for_updates: Whether to check for newer models in Azure ML

        Returns:
            Dict with sync results
        """
        results = {
            "baseline_downloaded": False,
            "dynamic_downloaded": False,
            "baseline_updated": False,
            "dynamic_updated": False,
        }

        if not self._azure_available:
            logger.info("Azure ML not available, using local weights only")
            return results

        baseline_path = self.weights_dir / "baseline_weights.pt"
        dynamic_path = self.weights_dir / "dynamic_weights.pt"

        # Download missing models
        if not baseline_path.exists():
            logger.info("Baseline model missing, downloading from Azure ML...")
            results["baseline_downloaded"] = self._download_model_from_azure(
                self.baseline_model_name, baseline_path
            )

        if not dynamic_path.exists():
            logger.info("Dynamic model missing, downloading from Azure ML...")
            results["dynamic_downloaded"] = self._download_model_from_azure(
                self.dynamic_model_name, dynamic_path
            )

        # Check for updates if requested
        if check_for_updates:
            results["baseline_updated"] = self._check_and_update_model(
                self.baseline_model_name, baseline_path
            )
            results["dynamic_updated"] = self._check_and_update_model(
                self.dynamic_model_name, dynamic_path
            )

        return results

    def _check_and_update_model(self, model_name: str, local_path: Path) -> bool:
        """Check if Azure ML has a newer version and update if so."""
        try:
            if not local_path.exists():
                return False

            # Get latest Azure ML model info
            azure_model = self._ml_client.models.get(model_name, label="latest")

            # Get local file modification time
            local_mtime = datetime.fromtimestamp(local_path.stat().st_mtime)
            azure_created = None
            if azure_model.creation_context:
                azure_created = azure_model.creation_context.created_at

            if azure_created and azure_created > local_mtime:
                logger.info(f"Newer {model_name} found in Azure ML, updating...")
                return self._download_model_from_azure(model_name, local_path)

        except Exception as e:
            logger.debug(f"Could not check for updates for {model_name}: {e}")

        return False

    def auto_upload_after_training(
        self,
        f1_score: float,
        auto_promote_threshold: float = 0.85,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, bool]:
        """
        Automatically upload dynamic model after training and optionally promote
        to baseline.

        Args:
            f1_score: F1 score achieved by the model
            auto_promote_threshold: F1 threshold for automatic promotion
            metadata: Additional metadata

        Returns:
            Dict with upload and promotion results
        """
        results = {"uploaded": False, "promoted": False}

        # Always upload the new model
        results["uploaded"] = self.upload_dynamic_model(f1_score, metadata)

        if results["uploaded"] and f1_score >= auto_promote_threshold:
            logger.info(
                f"F1 score {f1_score:.4f} >= threshold \
                    {auto_promote_threshold:.4f}, auto-promoting to baseline..."
            )
            results["promoted"] = self.promote_dynamic_to_baseline()

        return results

    def get_auto_sync_config(self) -> Dict[str, any]:
        """Get configuration for automatic sync behavior."""
        return {
            "auto_download_on_startup": True,
            "auto_check_updates_on_startup": True,
            "auto_upload_after_training": True,
            "auto_promote_threshold": 0.85,
            "sync_on_model_load": True,
            "background_sync_enabled": False,  # Future feature
        }
        """
        Find the baseline model with highest F1 score from Azure ML.

        Returns:
            Dict containing model info and F1 score, None if no models found
        """
        if not self._azure_available:
            logger.warning("Azure ML not available for baseline model search")
            return None

        try:
            # List all versions of the baseline model
            baseline_models = list(
                self._ml_client.models.list(name=self.baseline_model_name)
            )

            if not baseline_models:
                logger.info("No baseline models found in Azure ML")
                return None

            best_model = None
            best_f1 = -1.0

            logger.info(
                f"Evaluating {len(baseline_models)} baseline model versions "
                f"for best F1 score..."
            )

            for model in baseline_models:
                try:
                    # Extract F1 score from model tags
                    f1_str = model.tags.get("f1_score") if model.tags else None

                    if f1_str:
                        f1_score = float(f1_str)
                        logger.debug(
                            f"Model {model.name}:{model.version} has "
                            f"F1 score: {f1_score:.4f}"
                        )

                        if f1_score > best_f1:
                            best_f1 = f1_score
                            best_model = {
                                "model": model,
                                "f1_score": f1_score,
                                "version": model.version,
                                "name": model.name,
                            }
                    else:
                        logger.debug(
                            f"Model {model.name}:{model.version} "
                            f"has no F1 score tag"
                        )

                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid F1 score for model "
                        f"{model.name}:{model.version}: {e}"
                    )
                    continue

            if best_model:
                logger.info(
                    f"Best baseline model found: {best_model['name']}:"
                    f"{best_model['version']} with F1 score "
                    f"{best_model['f1_score']:.4f}"
                )
            else:
                logger.warning("No baseline models found with valid F1 scores")

            return best_model

        except Exception as e:
            logger.error(f"Error searching for best baseline model: {e}")
            return None

    def get_local_baseline_f1_score(self) -> Optional[float]:
        """
        Extract F1 score from local baseline model metadata.

        Returns:
            F1 score if found, None otherwise
        """
        try:
            # Check if sync status file exists with local model info
            sync_status_path = self.weights_dir / "sync_status.json"
            if sync_status_path.exists():
                with open(sync_status_path, "r") as f:
                    sync_data = json.load(f)

                # Look for baseline model F1 score in sync status
                baseline_info = (
                    sync_data.get("models", {})
                    .get("azure_ml", {})
                    .get("emotion-clf-baseline", {})
                )
                f1_str = baseline_info.get("tags", {}).get("f1_score")

                if f1_str:
                    return float(f1_str)

            # Fallback: check if there's a model_config.json with F1 info
            config_path = self.weights_dir / "model_config.json"
            if config_path.exists():
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    f1_str = config_data.get("f1_score")
                    if f1_str:
                        return float(f1_str)

            logger.debug("No local F1 score metadata found")
            return None

        except Exception as e:
            logger.warning(f"Error reading local baseline F1 score: {e}")
            return None

    def download_best_baseline_model(
        self, force_update: bool = False, min_f1_improvement: float = 0.01
    ) -> bool:
        """
        Download the best baseline model from Azure ML based on F1 comparison.

        Args:
            force_update: Download even if local F1 is equal or better
            min_f1_improvement: Minimum F1 improvement required to download

        Returns:
            True if model was downloaded and updated
        """
        if not self._azure_available:
            logger.info("Azure ML not available, keeping local baseline model")
            return False

        # Get the best model from Azure ML
        best_azure_model = self.get_best_baseline_model()
        if not best_azure_model:
            logger.info("No suitable baseline model found in Azure ML")
            return False

        azure_f1 = best_azure_model["f1_score"]
        baseline_path = self.weights_dir / "baseline_weights.pt"

        # Get local model F1 score for comparison
        local_f1 = self.get_local_baseline_f1_score()

        # Decide whether to download
        should_download = force_update

        if not should_download:
            if not baseline_path.exists():
                logger.info("Local baseline model missing, downloading from Azure")
                should_download = True
            elif local_f1 is None:
                logger.info(
                    "Local baseline F1 score unknown, "
                    "downloading latest from Azure ML"
                )
                should_download = True
            elif azure_f1 > (local_f1 + min_f1_improvement):
                logger.info(
                    f"Azure ML has better baseline model: "
                    f"F1 {azure_f1:.4f} vs local {local_f1:.4f}"
                )
                should_download = True
            else:
                logger.info(
                    f"Local baseline model is current: "
                    f"F1 {local_f1:.4f} vs Azure {azure_f1:.4f}"
                )

        if not should_download:
            return False

        # Download the best model
        model_info = best_azure_model["model"]
        logger.info(
            f"Downloading best baseline model {model_info.name}:"
            f"{model_info.version} with F1 score {azure_f1:.4f}"
        )

        success = self._download_specific_model_version(
            model_info.name, model_info.version, baseline_path
        )

        if success:
            # Update sync status with new model info
            self._update_sync_status_for_baseline(best_azure_model)
            logger.info(
                f"Successfully updated baseline model to version "
                f"{model_info.version} (F1: {azure_f1:.4f})"
            )

        return success

    def _download_specific_model_version(
        self, model_name: str, version: str, local_path: Path
    ) -> bool:
        """Download a specific model version from Azure ML."""
        try:
            # Download model to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                downloaded_path = self._ml_client.models.download(
                    name=model_name, version=version, download_path=temp_dir
                )

                # Handle case where download path might be None or temp_dir
                search_path = (
                    Path(downloaded_path) if downloaded_path else Path(temp_dir)
                )

                # Find the .pt file in downloaded content
                pt_files = list(search_path.rglob("*.pt"))

                if pt_files:
                    # Copy the first .pt file found to the target location
                    shutil.copy2(pt_files[0], local_path)

                    # Validate the downloaded model
                    if self._validate_downloaded_model(local_path):
                        file_size_mb = local_path.stat().st_size / (1024 * 1024)
                        logger.info(
                            f"✅ Downloaded and validated model: {local_path} "
                            f"({file_size_mb:.1f} MB)"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Downloaded model failed validation: {local_path}"
                        )
                        # Remove corrupted file
                        if local_path.exists():
                            local_path.unlink()
                        return False
                else:
                    logger.error(
                        f"No .pt file found in downloaded model "
                        f"{model_name}:{version}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error downloading model {model_name}:{version}: {e}")
            return False

    def _update_sync_status_for_baseline(self, model_info: Dict) -> None:
        """Update sync status file with baseline model information."""
        try:
            sync_status_path = self.weights_dir / "sync_status.json"

            # Load existing sync status or create new
            sync_data = {}
            if sync_status_path.exists():
                with open(sync_status_path, "r") as f:
                    sync_data = json.load(f)

            # Ensure structure exists
            if "models" not in sync_data:
                sync_data["models"] = {}
            if "azure_ml" not in sync_data["models"]:
                sync_data["models"]["azure_ml"] = {}
            if "emotion-clf-baseline" not in sync_data["models"]["azure_ml"]:
                sync_data["models"]["azure_ml"]["emotion-clf-baseline"] = {}

            # Update baseline model info
            model = model_info["model"]
            sync_data["models"]["azure_ml"]["emotion-clf-baseline"]["tags"] = {
                "f1_score": str(model_info["f1_score"]),
                "model_type": "baseline",
                "download_time": datetime.now().isoformat(),
                "version": model.version,
                "framework": (
                    model.tags.get("framework", "pytorch") if model.tags else "pytorch"
                ),
            }

            # Save updated sync status
            with open(sync_status_path, "w") as f:
                json.dump(sync_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Error updating sync status: {e}")

    def get_best_baseline_model(self) -> Optional[Dict]:
        """
        Find and return the best baseline model from Azure ML based on F1 score.

        Returns:
            Dictionary containing model info and F1 score, or None if no model found
        """
        if not self._azure_available:
            logger.warning("Azure ML not available")
            return None

        try:
            # Get all baseline models from Azure ML
            baseline_models = list(
                self._ml_client.models.list(name=self.baseline_model_name)
            )

            if not baseline_models:
                logger.info("No baseline models found in Azure ML")
                return None

            best_model = None
            best_f1_score = -1.0

            # Find model with highest F1 score
            for model in baseline_models:
                try:
                    # Extract F1 score from model tags
                    f1_score = 0.0
                    if model.tags and "f1_score" in model.tags:
                        f1_score = float(model.tags["f1_score"])
                    elif model.tags and "test_f1" in model.tags:
                        f1_score = float(model.tags["test_f1"])

                    if f1_score > best_f1_score:
                        best_f1_score = f1_score
                        best_model = model

                except (ValueError, TypeError):
                    logger.debug(
                        f"Could not parse F1 score for model \
                            {model.name}:{model.version}"
                    )
                    continue

            if best_model:
                logger.info(
                    f"Found best baseline model: \
                        {best_model.name}:{best_model.version} "
                    f"with F1 score {best_f1_score:.4f}"
                )
                return {"model": best_model, "f1_score": best_f1_score}
            else:
                logger.warning("No baseline models with valid F1 scores found")
                return None

        except Exception as e:
            logger.error(f"Error finding best baseline model: {e}")
            return None


# ============================================================================
# Module-level convenience functions for API usage
# ============================================================================


def sync_best_baseline(
    force_update: bool = False, min_f1_improvement: float = 0.0
) -> bool:
    """
    Convenience function for API startup - sync the best baseline model.

    This function provides a simple interface for the API to ensure it has the
    latest baseline model from Azure ML. It wraps the AzureMLSync class
    functionality with sensible defaults for API usage.

    Args:
        force_update: If True, downloads model even if local version exists
        min_f1_improvement: Minimum F1 score improvement required for update

    Returns:
        True if sync was successful or model is already up to date
    """
    logger = logging.getLogger(__name__)

    try:
        # Initialize Azure ML sync
        azure_sync = AzureMLSync("models/weights")

        if not azure_sync._azure_available:
            logger.warning("Azure ML not available for model sync")
            # Check if local baseline exists
            baseline_path = azure_sync.weights_dir / "baseline_weights.pt"
            if baseline_path.exists():
                logger.info("Using existing local baseline model")
                return True
            else:
                logger.error("No Azure ML connection and no local baseline model")
                return False

        # Ensure Azure ML client is properly initialized
        ml_client = azure_sync._get_ml_client()
        if ml_client is None:
            logger.warning("Failed to initialize Azure ML client")
            # Check if local baseline exists as fallback
            baseline_path = azure_sync.weights_dir / "baseline_weights.pt"
            if baseline_path.exists():
                logger.info("Using existing local baseline model (Azure client failed)")
                return True
            else:
                logger.error("No Azure ML client and no local baseline model")
                return False

        baseline_path = azure_sync.weights_dir / "baseline_weights.pt"

        # If force_update is True, always try to download latest
        if force_update:
            logger.info("Force update requested - downloading latest baseline")
            success = azure_sync._download_model_from_azure(
                azure_sync.baseline_model_name, baseline_path
            )
            if success:
                logger.info("✅ Force update completed successfully")
                azure_sync._update_local_sync_status()
                return True
            else:
                logger.warning("Force update failed, checking local model")
                return baseline_path.exists()

        # If baseline doesn't exist locally, download it
        if not baseline_path.exists():
            logger.info("Baseline missing locally - downloading from Azure")
            success = azure_sync._download_model_from_azure(
                azure_sync.baseline_model_name, baseline_path
            )
            if success:
                azure_sync._update_local_sync_status()
            return success

        # Baseline exists locally - consider it successful
        logger.info("Local baseline model is available")
        azure_sync._update_local_sync_status()
        return True

    except Exception as e:
        logger.error(f"Error during baseline model sync: {e}")
        return False
