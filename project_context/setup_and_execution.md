# Setup & Execution Guide

## Initial Setup
### 1. Clone and enter project
```bash
git clone git@github.com:shilarajpurohit-spec/oma.git
cd oma
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

## Running the Servers

### Backend Server
```bash
cd backend
uvicorn main:app --reload --port 8000
```
This will start the API at `http://localhost:8000`. API Docs are accessible at `http://localhost:8000/docs`.

### Frontend Server
```bash
cd frontend
npm install
npm run dev
```
By default, the Vite dev server runs at `http://localhost:5173`. Make sure the backend is simultaneously running.

## Docker (Single-Command Start)
```bash
# Build and start both services
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```
The frontend Nginx config proxies `/api/*` requests to the backend automatically.

## Executing Tests
- **Backend Tests**: 
  ```bash
  venv/bin/pytest backend/tests/ -v
  ```
- **Backend Integration Tests**:
  ```bash
  venv/bin/pytest backend/tests/test_integration.py -v
  ```
- **Frontend Tests**: 
  ```bash
  cd frontend
  npm run test
  ```
