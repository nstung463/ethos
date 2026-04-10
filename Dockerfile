FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[open-terminal]"

# Create workspace and logs directories
RUN mkdir -p workspace logs

# Expose API port
EXPOSE 8080

# Run Ethos API server
CMD ["python", "main.py"]
