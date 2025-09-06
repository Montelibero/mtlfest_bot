# Stage 1: Build the virtual environment
FROM python:3.12-slim as builder

# Install uv
RUN pip install uv

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Create the final image
FROM python:3.12-slim

# Install system dependencies for opencv and pyzbar
RUN apt-get update && apt-get install -y libgl1-mesa-glx libzbar0 && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set the path to the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . .

# Set the python path
ENV PYTHONPATH=.

# Command to run the application
CMD ["uv", "run", "main.py"]
