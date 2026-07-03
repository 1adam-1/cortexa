FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    gcc \
    g++ \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HF_API_TOKEN=""
ENV GEMINI_API_KEY=""
ENV JWT_SECRET_KEY=""
ENV DATABASE_URL=""

ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/models

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "300", "app:app"]