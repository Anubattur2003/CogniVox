# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add uvicorn and FastAPI
RUN pip install fastapi uvicorn python-multipart

# Copy the current directory contents into the container
COPY . .

# Make sure the scripts are executable
RUN chmod +x bin/cognivox

# Set environment variable to run in production mode
ENV COGNIVOX_ENV=production
ENV COGNIVOX_API_PORT=8000

# Expose the port the app runs on
EXPOSE 8000

# Command to run when the container starts
CMD ["python", "src/api/app.py"] 