FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port that the application runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"] 