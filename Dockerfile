FROM python:3.10.16-slim-bookworm

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
# Internal port (mapped to 5001 externally)
EXPOSE 5000

# Use gunicorn for production
# Use wsgi.py for Flask app factory pattern compatibility
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "wsgi:app"]
