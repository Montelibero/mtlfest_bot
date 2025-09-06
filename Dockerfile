# Use the official Python image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl libgl1-mesa-glx libzbar0 && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install uv and dependencies in one step
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:${PATH}" && \
    uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the python path
ENV PYTHONPATH=.

# Set the PATH for the CMD instruction
ENV PATH="/root/.local/bin:${PATH}"

# Command to run the application
CMD ["uv", "run", "main.py"]
