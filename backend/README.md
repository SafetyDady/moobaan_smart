# Moobaan Smart Backend

FastAPI backend service for the Moobaan Smart application.

## Local Development

### Option 1: Run with Python Virtual Environment

1. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Run with Docker Compose

From the root directory:
```bash
docker-compose -f docker/docker-compose.yml up backend
```

## Endpoints

- **Health Check**: GET `http://localhost:8000/health`
  - Returns: `{"status": "ok"}`

- **Root**: GET `http://localhost:8000/`
  - Returns: `{"name": "moobaan_smart_backend", "status": "running"}`

## Environment Variables

Copy `.env.example` to `.env` and modify as needed:
- `APP_NAME`: Application name
- `ENV`: Environment (local, development, production)
- `PORT`: Port to run the server on

## Production Deployment

The Dockerfile is configured for Railway deployment with automatic PORT injection.