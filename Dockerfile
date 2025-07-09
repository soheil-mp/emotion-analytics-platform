# 1. Parent image: Official Python 3.11-slim
FROM python:3.11-slim

# 2. Environment variables
# No .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Unbuffered Python output
ENV PYTHONUNBUFFERED=1

# 3. Working directory
WORKDIR /app

# 4. Install Poetry (pinned version)
RUN pip install poetry==1.8.3

# 5. Configure Poetry: Disable virtualenv creation in container
RUN poetry config virtualenvs.create false

# 6. Install system dependencies (ffmpeg, git, git-lfs)
# Cleans apt cache to reduce image size.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    git-lfs && \
    git lfs install --system && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 7. Copy dependency definitions (for Docker cache)
COPY pyproject.toml ./

# 8. Install project dependencies via Poetry
# --no-root: Don't install project itself; --only main: Main dependencies only
RUN poetry install --no-interaction --no-ansi --no-root --only main && \
    poetry cache clear --all . && \
    pip cache purge

# 8a. Install PyTorch with CUDA 12.1 support
# Adjust 'cu121' for other CUDA versions (e.g., cu118) or 'cpu' for CPU-only.
# IMPORTANT for GPU usage:
#   - The 'python:3.11-slim' base image does NOT include NVIDIA drivers/toolkit.
#   - Host machine needs NVIDIA drivers & NVIDIA Container Toolkit.
#   - Container must be run with GPU access (e.g., 'docker run --gpus all').
#   - PyTorch will fall back to CPU if these GPU requirements are not met.
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip cache purge

# 9. Download NLTK resources
# vader_lexicon (sentiment), punkt (tokenization), averaged_perceptron_tagger (POS tagging)
ENV NLTK_DATA=/app/nltk_data
RUN python -m nltk.downloader -d /app/nltk_data vader_lexicon punkt averaged_perceptron_tagger punkt_tab && \
    find /app/nltk_data -name "*.zip" -delete

# Set PYTHONPATH to include /app
ENV PYTHONPATH /app

# 10. Copy application code and models
COPY ./src/emotion_clf_pipeline /app/emotion_clf_pipeline
COPY ./models /app/models
COPY ./.env /app/.env

# 11. Clean up any remaining caches and temporary files
RUN find /app -type d -name "__pycache__" -exec rm -rf {} + || true && \
    find /app -name "*.pyc" -delete || true && \
    rm -rf /tmp/* /var/tmp/* /root/.cache/*

# 12. Expose port 3120
EXPOSE 3120

# 13. Startup command: Uvicorn serving FastAPI app
# --host 0.0.0.0 for external access
ENTRYPOINT ["uvicorn", "emotion_clf_pipeline.api:app", "--host", "0.0.0.0", "--port", "3120"]
