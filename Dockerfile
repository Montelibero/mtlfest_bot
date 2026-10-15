# syntax=docker/dockerfile:1
FROM python:3.14-slim

# Runtime system deps:
#   libzbar0t64 - native zbar library for pyzbar (QR decode fallback)
RUN apt-get update && apt-get install -y --no-install-recommends curl libzbar0t64 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Version metadata, baked at build time (CI passes GIT_SHA; local builds get "dev")
ARG GIT_SHA=dev
ENV GIT_SHA=${GIT_SHA}

# Install dependencies into the system interpreter (no venv games at runtime)
COPY requirements.txt .
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:${PATH}" && \
    uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application code
COPY . .

ENV PYTHONPATH=/app

CMD ["python", "main.py"]
