# Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Node.js 20+
- Python 3.13

## Local Development
1. Clone the repository.
2. Setup backend: `cd backend && python -m venv .venv && pip install -r requirements.txt && uvicorn app.main:app --reload`
3. Setup frontend: `cd frontend && npm install && npm run dev`

## Production Deployment
1. Set up your `.env` file with necessary API keys.
2. Navigate to `backend/deploy` and run `docker-compose up -d`.
3. Build and deploy frontend via Docker or a static host (Vercel/Netlify).
