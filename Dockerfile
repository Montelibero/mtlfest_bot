# Use the official Python image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl libgl1-mesa-glx libzbar0 && \
    rm -rf /var/lib/apt/lists/*

# Install uv using the recommended installer
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the python path
ENV PYTHONPATH=.

# Command to run the application
CMD ["uv", "run", "main.py"]
