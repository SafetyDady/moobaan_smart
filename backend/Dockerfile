FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port (Railway will inject PORT env var)
EXPOSE ${PORT:-8000}

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}