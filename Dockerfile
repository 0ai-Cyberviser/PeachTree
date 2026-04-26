FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install PeachTree in production mode
RUN pip install --no-cache-dir -e .

# Set up entrypoint
ENTRYPOINT ["peachtree"]
CMD ["--help"]
