FROM python:3.11-slim

WORKDIR /app

# Build timestamp - force rebuild (Apr 24, 2026 12:01 PM)
RUN echo "Build time: $(date)"

# Copy requirements first (before code) so changes to code don't invalidate pip cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --worker-class gthread --worker-tmp-dir /dev/shm main:app
