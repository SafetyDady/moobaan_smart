# Moobaan Smart - Monorepo

A modern web application for managing smart home communities (moobaan) with billing and administrative features.

## Project Structure

```
moobaan_smart/
├── backend/           # FastAPI backend service
│   ├── app/
│   │   ├── main.py    # FastAPI application
│   │   ├── api/       # API routes
│   │   └── core/      # Core configurations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/          # Vite React frontend
│   ├── src/
│   │   ├── main.jsx
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── docker/
│   └── docker-compose.yml
└── README.md
```

## Quick Start

### Option A: Run Services Separately

#### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Option B: Run with Docker Compose

```bash
cd docker
docker-compose up
```

This will start both services:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## Health Check URLs

- **Backend Health**: http://localhost:8000/health
- **Backend Root**: http://localhost:8000/
- **Frontend**: http://localhost:5173

## Development

The frontend includes a "Check Backend Health" button that tests the connection to the backend API.

### API Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Application info endpoint

## Deployment

- **Backend**: Dockerfile configured for Railway deployment
- **Frontend**: Optimized for Vercel deployment

## Next Steps

This is Phase 0 - a minimal but production-shaped scaffold. Future phases will include:
- Authentication system
- Database integration  
- Invoice management
- User management
- Advanced billing features