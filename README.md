# LegiFlow

## Local development

1. Copy `.env.example` to `.env` and set values as needed.
2. Run `docker compose up --build`.
3. Open `http://localhost:5173`; the backend health endpoint is at `http://localhost:8000/health`.

## Deployment

- **Render backend:** root directory `backend`, Docker runtime. Render supplies `PORT`; configure `CORS_ORIGINS` with the Vercel URL and `NIM_*` variables.
- **Vercel frontend:** root directory `frontend`; set `VITE_API_URL` to the Render backend URL (without a trailing slash).
