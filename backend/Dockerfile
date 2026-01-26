FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements - PostgreSQL + psycopg v3 ONLY
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy startup and seed scripts
COPY startup.py ./
COPY seed_users.py ./

# Expose port (Railway will inject PORT env var)
EXPOSE ${PORT:-8000}

# Run startup script (handles fresh DB) then start the application
CMD ["sh", "-c", "python startup.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]