# syntax=docker/dockerfile:1
FROM python:3.14-slim

# Runtime system deps:
#   libzbar0t64 - native zbar library for pyzbar (QR decode fallback)
RUN apt-get update && apt-get install -y --no-install-recommends curl libzbar0t64 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:${PATH}" && \
    uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application code
COPY . .

ENV PYTHONPATH=/app
ENV PATH="/root/.local/bin:${PATH}"

CMD ["uv", "run", "main.py"]
