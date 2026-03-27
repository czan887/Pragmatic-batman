# Project Instructions for Claude

## Package Management

- **Always install Python dependencies in virtual environments**
  - Use `./backend/venv/Scripts/pip install <package>` for the backend
  - Never use global pip install

- **Node packages should be installed in project directories**
  - Use `npm install` within the frontend directory

## Project Structure

- `backend/` - FastAPI backend with Playwright automation
- `backend/venv/` - Backend API virtual environment
- `frontend/` - React frontend (Vite + TypeScript)

## Running the Application

- Backend: `cd backend && ./venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8000`
- Frontend: `cd frontend && npm run dev`

## Git Commits

- **Never include "Co-Authored-By" or any authored-by Claude messages in commits**
