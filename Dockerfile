FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Install common dependencies with caching
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -qqy && \
    apt-get install -y --no-install-recommends \
        ssh \
        git \
        gcc \
        g++ \
        poppler-utils \
        libpoppler-dev \
        unzip \
        curl \
        cargo && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Create working directory
WORKDIR /app

# Lite version
FROM base AS lite

ARG TARGETARCH
ENV TARGETARCH=${TARGETARCH}

# Download PDF.js (cache this layer)
COPY scripts/download_pdfjs.sh /app/scripts/download_pdfjs.sh
RUN chmod +x /app/scripts/download_pdfjs.sh
ENV PDFJS_PREBUILT_DIR="/app/libs/ktem/ktem/assets/prebuilt/pdfjs-dist"
RUN bash /app/scripts/download_pdfjs.sh ${PDFJS_PREBUILT_DIR}

# Install Python dependencies (cache pip downloads)
COPY libs/kotaemon /app/libs/kotaemon
COPY libs/ktem /app/libs/ktem
RUN --mount=type=ssh \
    --mount=type=cache,target=/root/.cache/pip \
    pip install -e "libs/kotaemon" \
    && pip install -e "libs/ktem" \
    && pip install "pdfservices-sdk@git+https://github.com/niallcm/pdfservices-python-sdk.git@bump-and-unfreeze-requirements" \
    && pip install "fastapi[standard]" && \
    if [ "${TARGETARCH}" = "amd64" ]; then pip install "graphrag<=0.3.6" future; fi

# Copy remaining app code
COPY . /app

# Clean pip cache
RUN rm -rf ~/.cache/pip

# Default command
CMD ["fastapi", "run", "api/main.py", "--host", "0.0.0.0", "--port", "8000"]

# Full version
FROM lite AS full

# Install extra system packages
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -qqy && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-jpn \
        libsm6 \
        libxext6 \
        libreoffice \
        ffmpeg \
        libmagic-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install heavy Python dependencies with caching
RUN --mount=type=ssh \
    --mount=type=cache,target=/root/.cache/pip \
    pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cpu

RUN --mount=type=ssh \
    --mount=type=cache,target=/root/.cache/pip \
    pip install -e "libs/kotaemon[adv]" \
                unstructured[all-docs] \
                aioboto3 nano-vectordb ollama xxhash "lightrag-hku<=1.3.0" \
                "docling"

# Trigger NLTK data download via LlamaIndex
RUN python -c "from llama_index.core.readers.base import BaseReader"

# Clean pip cache
RUN rm -rf ~/.cache/pip