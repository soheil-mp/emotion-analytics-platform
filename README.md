
<div align="center">

<h1 style="color: #2563eb; margin-bottom: 10px;">Emotion Classification Pipeline</h1>

<p style="font-size: 18px; color: #64748b; margin-bottom: 20px;">
  <strong>Advanced NLP tool for extracting emotional insights from video and audio content</strong>
</p>

<div style="margin: 20px 0;">
  <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python 3.11">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/packaging-poetry-cyan.svg" alt="Poetry">
  <br>

  [![Lint Code](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/lint.yaml/badge.svg)](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/lint.yaml)
  [![Test Suite](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/test.yaml/badge.svg)](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/test.yaml)
  [![Docker Image (Build & Push)](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/docker-image.yml/badge.svg)](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/docker-image.yml)
  [![Sphinx Docs (Build & Deploy)](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/sphinx-docs.yml/badge.svg)](https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6/actions/workflows/sphinx-docs.yml)

</div>

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2px; border-radius: 15px; margin: 30px auto; max-width: 800px;">
  <img src="./assets/dashboard_screenshot.png" alt="Dashboard Preview" style="width: 100%; border-radius: 13px; display: block;">
</div>

<div style="margin: 30px 0;">
  <a href="https://bredauniversityadsai.github.io/2024-25d-fai2-adsai-group-nlp6/" style="background: #8b5cf6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; margin: 0 10px; font-weight: 600;">Documentation Webpage</a>
</div>

</div>

<br>

## Overview

Transform unstructured video and audio content into meaningful emotional analytics using our state-of-the-art NLP pipeline. Built with DeBERTa models and deployed on Azure ML, this system provides **dual-mode prediction** - choose between fast local inference or high-accuracy cloud processing with automatic NGROK URL conversion (no VPN required). Perfect for content analysis, customer sentiment tracking, and research applications.

## 🚀 Key Features

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">

<div style="border: 2px solid #10b981; border-radius: 12px; padding: 20px; background: #ecfdf5;">
  <h4 style="color: #047857; margin-top: 0;">⚡ Local Prediction</h4>
  <ul>
    <li><strong>Fast inference</strong> - On-premise processing</li>
    <li><strong>No network dependency</strong> - Works offline</li>
    <li><strong>Privacy-first</strong> - Data stays local</li>
    <li><strong>Low latency</strong> - Instant results</li>
  </ul>
</div>

<div style="border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; background: #eff6ff;">
  <h4 style="color: #1d4ed8; margin-top: 0;">☁️ Azure Cloud Prediction</h4>
  <ul>
    <li><strong>High accuracy</strong> - Latest trained models</li>
    <li><strong>Auto NGROK conversion</strong> - No VPN required</li>
    <li><strong>Scalable</strong> - Cloud infrastructure</li>
    <li><strong>Always updated</strong> - Latest model weights</li>
  </ul>
</div>

</div>

## Project Structure

```bash
./
├── .github/                         # GitHub Actions CI/CD workflows
├── .azuremlignore                   # Azure ML ignore patterns
├── .dockerignore                    # Docker build ignore patterns
├── .flake8                          # Python linting configuration
├── .gitignore                       # Git ignore rules
├── .pre-commit-config.yaml          # Pre-commit hook configurations
├── assets/                          # Static assets (images, logos, screenshots)
├── data/                            # Datasets and data processing
├── dist/                            # Distribution files (build artifacts)
├── docs/                            # Sphinx documentation
├── environment/                     # Environment configurations
├── frontend/                        # React.js web application
├── logs/                            # Application and system logs
├── mlruns/                          # MLflow experiment tracking
├── models/                          # Machine learning models and artifacts
├── monitoring/                      # Infrastructure monitoring
├── notebooks/                       # Jupyter notebooks for exploration
├── outputs/                         # Generated outputs and artifacts
├── results/                         # Experiment results and analysis
├── src/                             # Main source code
│   └── emotion_clf_pipeline/        # Core Python package
│       ├── __init__.py              # Package initialization
│       ├── api.py                   # FastAPI web service
│       ├── azure_endpoint.py        # Azure ML endpoint integration
│       ├── azure_hyperparameter_sweep.py # HPT on Azure ML
│       ├── azure_pipeline.py        # Azure ML pipeline orchestration
│       ├── azure_score.py           # Azure ML scoring functions
│       ├── azure_sync.py            # Azure ML synchronization
│       ├── cli.py                   # Command-line interface
│       ├── data.py                  # Data loading and preprocessing
│       ├── features.py              # Feature engineering
│       ├── model.py                 # DeBERTa model architecture
│       ├── monitoring.py            # System monitoring and metrics
│       ├── predict.py               # Prediction pipeline
│       ├── stt.py                   # Speech-to-text processing
│       ├── train.py                 # Model training pipeline
│       ├── transcript.py            # Transcript processing
│       ├── transcript_translator.py # Multi-language transcript support
│       └── translator.py            # Text translation utilities
├── tests/                           # Comprehensive test suite
├── docker-compose.yml               # Multi-container orchestration
├── docker-compose.build.yml         # Build-specific container config
├── Dockerfile                       # Backend container configuration
├── LICENSE                          # MIT license
├── poetry.lock                      # Poetry dependency lock file
├── pyproject.toml                   # Python project configuration (Poetry)
├── start-build.bat                  # Windows build script
├── start-production.bat             # Windows production deployment
└── README.md                        # This comprehensive documentation
```

<br>

## Quick Start

### Prerequisites
- **Python 3.11+**
- **Docker** (recommended)
- **Poetry** for dependency management

### 1. Clone & Setup

```bash
git clone https://github.com/BredaUniversityADSAI/2024-25d-fai2-adsai-group-nlp6.git
cd 2024-25d-fai2-adsai-group-nlp6
```

### 2. Environment Configuration

Create `.env` file in the project root:

```bash
# Required API Keys
ASSEMBLYAI_API_KEY="your_assemblyai_key"
GEMINI_API_KEY="your_gemini_key"

# Azure ML Configuration (Optional - for cloud predictions)
AZURE_SUBSCRIPTION_ID="your_subscription_id"
AZURE_RESOURCE_GROUP="buas-y2"
AZURE_WORKSPACE_NAME="NLP6-2025"
AZURE_LOCATION="westeurope"
AZURE_TENANT_ID="your_tenant_id"
AZURE_CLIENT_ID="your_client_id"
AZURE_CLIENT_SECRET="your_client_secret"

# Azure ML Endpoint (automatically converts private URLs to NGROK)
AZURE_ENDPOINT_URL="http://194.171.191.227:30526/api/v1/endpoint/deberta-emotion-clf-endpoint/score"
AZURE_API_KEY="your_azure_endpoint_key"
```

### 3. Launch Application

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">

<div style="border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; background: #eff6ff;">
  <h4 style="color: #1d4ed8; margin-top: 0;">🐳 Docker (Recommended)</h4>
  <p>Complete full-stack deployment:</p>
  <pre style="background: #1e293b; color: #e2e8f0; padding: 10px; border-radius: 6px; margin: 10px 0;"><code>docker-compose up --build</code></pre>
  <p><strong>Access:</strong><br>
  • Frontend: <code>http://localhost:3121</code><br>
  • API: <code>http://localhost:3120</code></p>
</div>

<div style="border: 2px solid #10b981; border-radius: 12px; padding: 20px; background: #ecfdf5;">
  <h4 style="color: #047857; margin-top: 0;">💻 Development Mode</h4>
  <p>For development and debugging:</p>
  <pre style="background: #1e293b; color: #e2e8f0; padding: 10px; border-radius: 6px; margin: 10px 0;"><code>poetry install && poetry shell
uvicorn src.emotion_clf_pipeline.api:app --reload</code></pre>
  <p><strong>CLI Usage:</strong></p>
  <pre style="background: #1e293b; color: #e2e8f0; padding: 10px; border-radius: 6px; margin: 10px 0;"><code>python -m emotion_clf_pipeline.cli predict "YOUTUBE_URL"</code></pre>
</div>

</div>

### 4. API Usage Examples

**Dual-Mode API**: Choose between fast local inference or high-accuracy cloud prediction.

**Local Prediction** (Fast, on-premise):
```bash
# cURL example
curl -X POST "http://localhost:3120/predict" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "method": "local"}'

# PowerShell example (Windows)
Invoke-RestMethod -Uri "http://localhost:3120/predict" -Method POST \
  -ContentType "application/json" \
  -Body '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "method": "local"}'
```

**Azure Prediction** (High-accuracy, cloud-based with automatic NGROK conversion):
```bash
# cURL example
curl -X POST "http://localhost:3120/predict" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "method": "azure"}'

# PowerShell example (Windows)
Invoke-RestMethod -Uri "http://localhost:3120/predict" -Method POST \
  -ContentType "application/json" \
  -Body '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "method": "azure"}'
```

**Python SDK Examples:**

```python
import requests

# Local prediction (fast)
response = requests.post(
    "http://localhost:3120/predict",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "method": "local"}
)
emotions = response.json()

# Azure prediction (high-accuracy, automatic NGROK conversion)
response = requests.post(
    "http://localhost:3120/predict",
    json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "method": "azure"}
)
emotions = response.json()
```

<br>

## 🗺️ Architecture Diagrams

This section provides an overview of the system's architecture and data flow.

### System Architecture (High-Level)

This diagram illustrates the main components of the Emotion Classification Pipeline and how they interact, including user interfaces, backend services, external dependencies, and data storage.

```mermaid
graph TD
    subgraph User Interaction
        UI[Browser - React Frontend]
        CLI[Command Line Interface]
        CURL[cURL/Postman]
    end

    subgraph Backend Services [Emotion Classification Pipeline API - FastAPI]
        API[api.py - Endpoints /predict, /health]
        PRED[predict.py - Orchestration Logic]
        DATA[data.py - Data Handling]
        MODEL[model.py - Emotion Model]
    end

    subgraph External Services
        YT[YouTube API/Service]
        ASSEMBLY[AssemblyAI API]
        WHISPER[Whisper Model - Local/HuggingFace]
    end

    subgraph Data Storage
        DS_AUDIO[Local File System: /data/youtube_audio]
        DS_TRANS[Local File System: /data/transcripts]
        DS_RESULTS[Local File System: /data/results]
    end

    UI --> API
    CLI --> PRED
    CURL --> API

    API --> PRED

    PRED --> DATA
    PRED --> MODEL
    PRED --> ASSEMBLY
    PRED --> WHISPER

    DATA --> YT
    DATA --> DS_AUDIO
    ASSEMBLY --> DS_TRANS
    WHISPER --> DS_TRANS
    MODEL --> DS_RESULTS


    classDef userStyle fill:#C9DAF8,stroke:#000,stroke-width:2px,color:#000
    class UI,CLI,CURL userStyle

    classDef backendStyle fill:#D9EAD3,stroke:#000,stroke-width:2px,color:#000
    class API,PRED,DATA,MODEL backendStyle

    classDef externalStyle fill:#FCE5CD,stroke:#000,stroke-width:2px,color:#000
    class YT,ASSEMBLY,WHISPER externalStyle

    classDef storageStyle fill:#FFF2CC,stroke:#000,stroke-width:2px,color:#000
    class DS_AUDIO,DS_TRANS,DS_RESULTS storageStyle
```

### Data Flow for `/predict` Endpoint

This sequence diagram details the process from a user submitting a YouTube URL to receiving the emotion analysis results. It highlights the interactions between the frontend, backend API, prediction service, data handling, transcription, and the emotion model.

```mermaid
sequenceDiagram
    actor User
    participant Frontend_UI as Frontend UI (React)
    participant Backend_API as FastAPI Backend (api.py)
    participant PredictionService as Prediction Service (predict.py)
    participant DataHandler as Data Handler (data.py)
    participant TranscriptionService as Transcription (AssemblyAI/Whisper)
    participant EmotionModel as Emotion Model (model.py)
    participant FileSystem as Local File System (data/*)

    User->>Frontend_UI: Inputs YouTube URL
    Frontend_UI->>Backend_API: POST /predict (URL)
    activate Backend_API

    Backend_API->>PredictionService: process_youtube_url_and_predict(URL)
    activate PredictionService

    PredictionService->>DataHandler: save_youtube_audio(URL)
    activate DataHandler
    DataHandler-->>FileSystem: Saves audio.mp3
    DataHandler-->>PredictionService: Returns audio_file_path
    deactivate DataHandler

    PredictionService->>TranscriptionService: Transcribe(audio_file_path)
    activate TranscriptionService
    TranscriptionService-->>FileSystem: Saves transcript.xlsx/json
    TranscriptionService-->>PredictionService: Returns transcript_data (text, timestamps)
    deactivate TranscriptionService

    PredictionService->>EmotionModel: predict_emotion(transcript_sentences)
    activate EmotionModel
    EmotionModel-->>PredictionService: Returns emotion_predictions (emotion, sub_emotion, intensity)
    deactivate EmotionModel

    PredictionService-->>FileSystem: Saves results.xlsx (optional)
    PredictionService-->>Backend_API: Formatted JSON with predictions
    deactivate PredictionService

    Backend_API-->>Frontend_UI: JSON Response
    deactivate Backend_API
    Frontend_UI->>User: Displays emotional analysis
```

### Internal Component Diagram (`src/emotion_clf_pipeline`)

This diagram shows the primary Python modules within the `src/emotion_clf_pipeline` package and their main dependencies, focusing on the prediction pathway.

```mermaid
graph LR
    subgraph src/emotion_clf_pipeline
        A[api.py]
        B[cli.py]
        C[predict.py]
        D[model.py]
        E[data.py]
        F[train.py] -- Not directly in /predict flow --> D
    end

    A --> C
    B --> C
    C --> D
    C --> E

    D --> E


    classDef moduleStyle fill:#E6E6FA,stroke:#333,stroke-width:2px,color:#000
    class A,B,C,D,E,F moduleStyle
```

### System Components

<table style="width: 100%; border-collapse: collapse;">
  <tr>
    <th style="background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; text-align: left;">Component</th>
    <th style="background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; text-align: left;">Technology</th>
    <th style="background: #f8fafc; padding: 15px; border: 1px solid #e2e8f0; text-align: left;">Purpose</th>
  </tr>
  <tr>
    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>Frontend</strong></td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">React.js</td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">Interactive web interface</td>
  </tr>
  <tr>
    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>API</strong></td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">FastAPI</td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">REST endpoints and validation</td>
  </tr>
  <tr>
    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>ML Pipeline</strong></td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">DeBERTa + PyTorch</td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">Emotion classification</td>
  </tr>
  <tr>
    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>Speech Processing</strong></td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">AssemblyAI / Whisper</td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">Audio transcription</td>
  </tr>
  <tr>
    <td style="padding: 15px; border: 1px solid #e2e8f0;"><strong>Cloud Platform</strong></td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">Azure ML</td>
    <td style="padding: 15px; border: 1px solid #e2e8f0;">Training & deployment</td>
  </tr>
</table>

<br>

## Common Commands

 There are two ways to interact with the code. To either process them on premise or on cloud. Below you can see a comprehensive guideline on how to use various commands on both option.

### Option 1 - On Premise

`Data preprocessing`: Preprocess the data and save them in the specified location.
```bash
python -m emotion_clf_pipeline.cli preprocess --verbose --raw-train-path "data/raw/train" --raw-test-path "data/raw/test/test_data-0001.csv"
```

`Train and evaluate`: Train the model and evaluate it on various data splits, which includes model syncing with Azure model (i.e., first downloading the best model from azure, and finally registering the weight to Azure model):
```bash
python -m emotion_clf_pipeline.cli train --epochs 15 --learning-rate 1e-5 --batch-size 16
```

`Prediction`: There are various methods when it comes to get the prediction:
```bash
# Option 1 - API (Dual-Mode: Local or Azure)
uvicorn src.emotion_clf_pipeline.api:app --host 0.0.0.0 --port 3120 --reload    # Start backend api

# Local prediction API call:
Invoke-RestMethod -Uri "http://127.0.0.1:3120/predict" -Method POST -ContentType "application/json" -Body '{"url": "YOUTUBE-LINK", "method": "local"}'

# Azure prediction API call (with automatic NGROK conversion):
Invoke-RestMethod -Uri "http://127.0.0.1:3120/predict" -Method POST -ContentType "application/json" -Body '{"url": "YOUTUBE-LINK", "method": "azure"}'

# Option 2 - CLI
python -m emotion_clf_pipeline.cli predict "YOUTUBE-LINK"

# Option 3 - Docker container (backend only)
docker build -t emotion-clf-api .
docker run -p 3120:80 emotion-clf-api

# Option 4 - Docker compose (both frontend and backend)
docker-compose up --build
```

### Option 2 - On Cloud (Azure)

`Data preprocessing job`: It takes the data from 'emotion-raw-train' and 'emotion-raw-test' and then registered the final preprocessed data into 'emotion-processed-train' and 'emotion-processed-test'
```bash
poetry run python -m emotion_clf_pipeline.cli preprocess --azure --register-data-assets --verbose
```

`Training job`: It takes the preprocessed data and train the model using them, evaluate them, and finally register the weights.
```bash
poetry run python -m emotion_clf_pipeline.cli train --azure --verbose
```

`Full pipeline`: This is the combination of data and train pipeline from above.
```bash
poetry run python -m emotion_clf_pipeline.cli pipeline --azure --verbose
```

`Scheduled pipeline`: This command create a schedule for the full pipeline on the specified time schedule.
```bash
python -m src.emotion_clf_pipeline.cli schedule create --schedule-name 'scheduled-deberta-full-pipeline' --daily --hour 0 --minute 0 --enabled --mode azure
```

`Hyperparameter tunning sweep`: This create multiple sweeps for doing hyperparameter tunning.
```bash
poetry run python -m emotion_clf_pipeline.hyperparameter_tuning
```

`Prediction`: We can make a prediction on Azure ML Endpoint using this command.
```bash
python -m emotion_clf_pipeline.cli predict "YOUTUBE-LINK" --use-azure
python -m emotion_clf_pipeline.cli predict "https://youtube.com/watch?v=VIDEO_ID" --use-azure --use-ngrok
```

<br>

## Contributing

### Development Workflow

```bash
# Set up development environment
poetry install
poetry run pre-commit install

# Run quality checks
poetry run pre-commit run --all-files
poetry run pytest -v
```

### Branch Naming Convention

To ensure consistent collaboration and traceability, all branches should follow the naming convention:

```
<type>/<sprint>-<scope>-<action>
```

Example: `feature/s2-data-add-youtube-transcript`

Type Prefixes:

| Prefix     | Description                     |
| ---------- | ------------------------------- |
| `feature`  | New functionality               |
| `fix`      | Bug fixes                       |
| `test`     | Unit/integration testing        |
| `docs`     | Documentation updates           |
| `config`   | Environment or dependency setup |
| `chore`    | Maintenance and cleanup         |
| `refactor` | Code restructuring              |


### Pull Request Process

1. Create a feature branch
2. Make your changes
3. Submit a pull request
4. Wait for code review and approval

<br>

## Testing

### Running Tests

```bash
# All tests
poetry run pytest -v

# Specific test types
poetry run pytest tests/unit -v
poetry run pytest tests/integration -v

# With coverage
poetry run coverage run -m pytest
poetry run coverage report
poetry run coverage html
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **API Tests**: Test REST endpoint functionality

<br>

## Advanced Features

### Git LFS for Large Files

For managing large model files, configure Git LFS:

```bash
# Install and initialize Git LFS
git lfs install

# Track model files
git lfs track "models/*"

# Commit LFS configuration
git add .gitattributes && git commit -m "Configure Git LFS"
```

### Development Tools

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">

<div>
<h4>Code Quality</h4>

```bash
# Pre-commit hooks
poetry run pre-commit install
poetry run pre-commit run --all-files

# Linting
poetry run flake8 src/
poetry run black src/
```
</div>

<div>
<h4>Documentation</h4>

```bash
# Generate API docs
cd docs && make html

# Serve documentation
python -m http.server 8000 -d docs/_build/html
```
</div>

</div>

<br>

## License

This project is licensed under the **MIT License**.
