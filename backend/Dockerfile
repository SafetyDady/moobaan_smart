FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements - PostgreSQL + psycopg v3 ONLY
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy seed script for initial setup (optional)
COPY seed_users.py ./

# Expose port (Railway will inject PORT env var)
EXPOSE ${PORT:-8000}

# Run migrations and start the application
# Migrations run on every deploy to ensure DB schema is up-to-date
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}