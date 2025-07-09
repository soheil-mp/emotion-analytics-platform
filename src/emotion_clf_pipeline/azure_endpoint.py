#!/usr/bin/env python3
"""
Azure ML Endpoint Deployment Script
Deploys the emotion classification model as an Azure ML managed online endpoint.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

# Azure ML SDK v2 imports
from azure.ai.ml import MLClient
from azure.ai.ml.entities import (
    CodeConfiguration,
    Environment,
    KubernetesOnlineDeployment,
    KubernetesOnlineEndpoint,
    Model,
)
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AzureMLKubernetesDeployer:
    """
    Handles deployment of emotion classification model to Azure ML Kubernetes endpoint.

    Uses the simplified pattern from the working old module with DefaultAzureCredential
    and direct .wait() operations for better network compatibility.
    """

    K8S_INSTANCE_TYPES = ["defaultinstancetype"]

    def __init__(self, env_file: str = ".env"):
        """
        Initialize the deployer with Azure credentials using DefaultAzureCredential.

        Args:
            env_file: Path to environment file (used for workspace details)
        """
        self.endpoint_name = "deberta-emotion-clf-endpoint"
        self.deployment_name = "blue"  # Blue-green deployment pattern
        self.model_name = "deberta-endpoint-model"
        self.compute_name = "adsai-lambda-0"  # Kubernetes cluster name
        self.namespace = "nlp6"  # Kubernetes namespace
        self.instance_type = "defaultinstancetype"

        # Load environment for workspace details
        load_dotenv(env_file)
        self.ml_client = self._create_ml_client()

        workspace_name = os.getenv("AZURE_WORKSPACE_NAME", "NLP6-2025")
        logger.info(f"✅ Connected to Azure ML workspace: {workspace_name}")
        logger.info(
            f"🐳 Using Kubernetes cluster: {self.compute_name} "
            f"(namespace: {self.namespace}, instance_type: {self.instance_type})"
        )

    def _create_ml_client(self) -> MLClient:
        """Create authenticated Azure ML client using DefaultAzureCredential."""
        try:
            return MLClient(
                DefaultAzureCredential(),
                subscription_id=os.getenv(
                    "AZURE_SUBSCRIPTION_ID", "0a94de80-6d3b-49f2-b3e9-ec5818862801"
                ),
                resource_group_name=os.getenv("AZURE_RESOURCE_GROUP", "buas-y2"),
                workspace_name=os.getenv("AZURE_WORKSPACE_NAME", "NLP6-2025"),
            )
        except Exception as e:
            logger.error(f"Failed to initialize MLClient: {e}")
            raise

    def register_model(self, force_update: bool = False) -> Model:
        """
        Register the emotion classification model with Azure ML.

        Args:
            force_update: Whether to update if model already exists

        Returns:
            Registered model entity
        """
        logger.info(f"📦 Registering model: {self.model_name}")

        # Define model artifacts path relative to workspace root
        workspace_root = Path(__file__).parent.parent.parent
        model_path = workspace_root / "models"
        model_path = model_path.resolve()  # Convert to absolute path

        if not model_path.exists():
            raise FileNotFoundError(f"Model artifacts not found at: {model_path}")

        # Create model entity
        model = Model(
            name=self.model_name,
            path=model_path,
            description=(
                "DeBERTa-based emotion classification model with multi-task learning"
            ),
            tags={
                "framework": "pytorch",
                "model_type": "deberta-v3-xsmall",
                "task": "emotion_classification",
                "features": "tfidf+emolex",
                "version": "1.0",
            },
            properties={
                "emotion_classes": "7",
                "sub_emotion_classes": "28",
                "intensity_classes": "3",
                "feature_dim": "121",
                "hidden_dim": "256",
            },
        )

        try:
            registered_model = self.ml_client.models.create_or_update(model)
            logger.info(
                f"✅ Model registered successfully: "
                f"{registered_model.name}:{registered_model.version}"
            )
            return registered_model

        except ResourceExistsError:
            if force_update:
                logger.info("Model exists, updating...")
                registered_model = self.ml_client.models.create_or_update(model)
                return registered_model
            else:
                logger.info("Model already exists, using existing version")
                return self.ml_client.models.get(name=self.model_name, label="latest")

    def create_environment(self) -> Environment:
        """
        Create Azure ML environment optimized for deployment.

        Returns:
            Environment entity for the deployment
        """
        logger.info("🐳 Creating Azure ML environment")

        # Define conda file path relative to workspace root
        workspace_root = Path(__file__).parent.parent.parent
        conda_file_path = workspace_root / "environment" / "environment.yml"
        conda_file_path = conda_file_path.resolve()

        # Define environment with comprehensive dependencies
        environment = Environment(
            name="emotion-clf-pipeline-env",
            description=(
                "Custom environment for emotion classifier with all training "
                "and inference dependencies."
            ),
            image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
            conda_file=str(conda_file_path),
        )

        try:
            created_env = self.ml_client.environments.create_or_update(environment)
            logger.info(
                f"✅ Environment created: {created_env.name}:{created_env.version}"
            )
            return created_env

        except Exception as e:
            logger.warning(f"Environment creation failed, trying fallback: {e}")
            # Try to get existing environment - first try latest, then version 30
            try:
                existing_env = self.ml_client.environments.get(
                    name="emotion-clf-pipeline-env", label="latest"
                )
                logger.info(
                    f"✅ Using existing environment: "
                    f"{existing_env.name}:{existing_env.version}"
                )
                return existing_env
            except Exception as fallback_error:
                logger.warning(
                    f"Latest environment not found, trying version 30: "
                    f"{fallback_error}"
                )
                # Try to get version 30 specifically
                return self.ml_client.environments.get(
                    name="emotion-clf-pipeline-env", version="30"
                )

    def create_endpoint(self) -> None:
        """Create the Kubernetes endpoint if it doesn't exist."""
        try:
            self.ml_client.online_endpoints.get(self.endpoint_name)
            logger.info(f"Endpoint '{self.endpoint_name}' already exists.")
        except ResourceNotFoundError:
            logger.info(
                f"Endpoint '{self.endpoint_name}' not found, creating a new one."
            )
            endpoint = KubernetesOnlineEndpoint(
                name=self.endpoint_name, auth_mode="key", compute=self.compute_name
            )
            try:
                result = self.ml_client.online_endpoints.begin_create_or_update(
                    endpoint
                )
                result.wait()  # Use wait() for synchronous completion
                logger.info(f"✅ Kubernetes endpoint created: {self.endpoint_name}")
            except Exception as e:
                logger.error(
                    f"Failed to create endpoint '{self.endpoint_name}': {e}",
                    exc_info=True,
                )
                raise

    def create_deployment(self, model: Model, environment: Environment):
        """
        Create deployment for the Kubernetes endpoint.

        Args:
            model: Registered model entity
            environment: Environment entity

        Returns:
            Created deployment entity
        """
        return self._create_kubernetes_deployment(model, environment)

    def _create_kubernetes_deployment(
        self, model: Model, environment: Environment, retry: int = 3
    ) -> KubernetesOnlineDeployment:
        """Create Kubernetes deployment using the simplified working pattern."""
        logger.info(f"🚀 Creating Kubernetes deployment: {self.deployment_name}")

        for attempt in range(1, retry + 1):
            logger.info(
                f"Deployment attempt {attempt}/{retry} for '{self.deployment_name}'..."
            )
            try:
                deployment = KubernetesOnlineDeployment(
                    name=self.deployment_name,
                    endpoint_name=self.endpoint_name,
                    model=model,
                    environment=environment,
                    code_configuration=CodeConfiguration(
                        code=str(Path(__file__).parent), scoring_script="azure_score.py"
                    ),
                    instance_type=self.instance_type,
                    instance_count=1,
                )

                logger.info(f"Submitting deployment '{self.deployment_name}'...")
                result = self.ml_client.online_deployments.begin_create_or_update(
                    deployment
                )
                result.wait()  # Use wait() for synchronous completion

                logger.info(
                    f"✅ Kubernetes deployment created successfully: "
                    f"{self.deployment_name}"
                )
                return deployment

            except Exception as e:
                error_msg = str(e).lower()
                logger.warning(f"Deployment attempt {attempt} failed: {error_msg}")

                # Handle specific error cases
                if attempt < retry:
                    if (
                        "unrecoverable state" in error_msg
                        or "delete and re-create" in error_msg
                    ):
                        logger.warning(
                            f"Deployment '{self.deployment_name}' in unrecoverable "
                            f"state. Cleaning up and retrying..."
                        )
                        try:
                            self.ml_client.online_deployments.begin_delete(
                                endpoint_name=self.endpoint_name,
                                name=self.deployment_name,
                            ).wait()
                            time.sleep(10)  # Wait for cleanup
                        except Exception:
                            pass  # Ignore cleanup errors
                        continue

                    # General retry with backoff
                    time.sleep(5 * attempt)
                    continue
                else:
                    logger.error(
                        f"All deployment attempts for '{self.deployment_name}' "
                        f"failed after {retry} tries."
                    )
                    raise

    def set_traffic_allocation(self, traffic_percentage: int = 100) -> None:
        """
        Set traffic allocation for the deployment.

        Args:
            traffic_percentage: Percentage of traffic to route to this deployment
        """
        logger.info(f"🚦 Setting traffic allocation: {traffic_percentage}%")

        endpoint = self.ml_client.online_endpoints.get(name=self.endpoint_name)
        endpoint.traffic = {self.deployment_name: traffic_percentage}

        self.ml_client.online_endpoints.begin_create_or_update(endpoint).result()
        logger.info("✅ Traffic allocation updated")

    def test_endpoint(self) -> Dict[str, Any]:
        """
        Test the deployed endpoint with sample data.

        Returns:
            Test results dictionary
        """
        logger.info("🧪 Testing deployed endpoint")

        # Sample test data
        test_data = {
            "text": "I am feeling really happy and excited about this project!"
        }

        try:
            # Invoke the endpoint
            response = self.ml_client.online_endpoints.invoke(
                endpoint_name=self.endpoint_name,
                request_file=None,
                deployment_name=self.deployment_name,
                request_data=json.dumps(test_data),
            )

            result = json.loads(response)
            logger.info(f"✅ Endpoint test successful: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Endpoint test failed: {e}")
            raise

    def get_endpoint_details(self) -> Dict[str, Any]:
        """
        Get endpoint details including scoring URI and authentication keys.

        Returns:
            Dictionary containing endpoint details
        """
        try:
            endpoint = self.ml_client.online_endpoints.get(name=self.endpoint_name)
            keys = self.ml_client.online_endpoints.get_keys(name=self.endpoint_name)

            details = {
                "endpoint_name": endpoint.name,
                "scoring_uri": endpoint.scoring_uri,
                "swagger_uri": endpoint.openapi_uri,
                "state": endpoint.provisioning_state,
                "location": endpoint.location,
                "authentication": {
                    "auth_mode": endpoint.auth_mode,
                    "primary_key": keys.primary_key if keys else None,
                    "secondary_key": keys.secondary_key if keys else None,
                },
                "traffic_allocation": endpoint.traffic,
            }

            logger.info("📊 Endpoint details retrieved successfully")
            return details

        except Exception as e:
            logger.error(f"❌ Failed to get endpoint details: {e}")
            raise

    def deploy_complete_pipeline(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Deploy the complete ML pipeline end-to-end.

        Args:
            force_update: Whether to force update existing resources

        Returns:
            Deployment summary with endpoint details
        """
        logger.info("🚀 Starting complete pipeline deployment")

        try:
            # Step 1: Register model
            model = self.register_model(force_update=force_update)

            # Step 2: Create environment
            environment = self.create_environment()

            # Step 3: Create endpoint
            self.create_endpoint()

            # Step 4: Create deployment
            created_deployment = self.create_deployment(model, environment)

            # Step 5: Set traffic allocation
            self.set_traffic_allocation(100)

            # Step 6: Return deployment summary
            summary = {
                "endpoint": {
                    "name": self.endpoint_name,
                    "scoring_uri": self.get_endpoint_details()["scoring_uri"],
                    "state": "Succeeded",
                },
                "deployment": {
                    "name": created_deployment.name,
                    "state": "Succeeded",
                },
                "model": {
                    "name": model.name,
                    "version": model.version,
                },
                "environment": {
                    "name": environment.name,
                    "version": environment.version,
                },
            }

            logger.info("✅ Complete pipeline deployment successful")

            return summary

        except Exception as e:
            logger.error(f"❌ Pipeline deployment failed: {e}")
            raise

    def cleanup_endpoint(self) -> None:
        """Delete the endpoint and all associated deployments."""
        logger.info(f"🗑️ Cleaning up endpoint: {self.endpoint_name}")

        try:
            self.ml_client.online_endpoints.begin_delete(
                name=self.endpoint_name
            ).result()
            logger.info("✅ Endpoint deleted successfully")

        except ResourceNotFoundError:
            logger.info("Endpoint not found, nothing to delete")
        except Exception as e:
            logger.error(f"❌ Failed to delete endpoint: {e}")
            raise


def main():
    """Main deployment script entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deploy emotion classification model to Azure ML"
    )
    parser.add_argument(
        "--action",
        choices=["deploy", "test", "details", "cleanup"],
        default="deploy",
        help="Action to perform",
    )
    parser.add_argument(
        "--force-update", action="store_true", help="Force update existing resources"
    )

    args = parser.parse_args()

    # Initialize deployer
    deployer = AzureMLKubernetesDeployer()

    try:
        if args.action == "deploy":
            result = deployer.deploy_complete_pipeline(force_update=args.force_update)
            print(json.dumps(result, indent=2))

        elif args.action == "test":
            result = deployer.test_endpoint()
            print(json.dumps(result, indent=2))

        elif args.action == "details":
            details = deployer.get_endpoint_details()
            print(json.dumps(details, indent=2))

        elif args.action == "cleanup":
            deployer.cleanup_endpoint()
            print("Endpoint cleanup completed")

    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
