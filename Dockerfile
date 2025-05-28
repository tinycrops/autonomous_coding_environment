# ACE v2 - Safe Execution Environment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ACE v2 source code
COPY *.py ./
COPY README_v2.md ./

# Create directories for workspaces
RUN mkdir -p /app/workspaces

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN useradd -m -s /bin/bash aceuser
RUN chown -R aceuser:aceuser /app
USER aceuser

# Default command
CMD ["python", "ace_v2_enhanced.py"] 