# Use the official Python image
FROM python:3.12-slim

# Install uv and system dependencies
RUN pip install uv && \
    apt-get update && apt-get install -y libgl1-mesa-glx libzbar0 && \
    rm -rf /var/lib/apt/lists/*

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