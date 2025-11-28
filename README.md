# Lead Agent API

FastAPI backend for qualifying real-estate leads with JWT auth, lead scoring, properties, and multi-agency support.

## Setup
1. Create and activate a virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment in `.env` (Supabase-only, required):
   ```bash
   DATABASE_URL=postgresql+psycopg2://<supabase-user>:<supabase-password>@<host>:5432/postgres
   SECRET_KEY=change-me
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   JWT_ALGORITHM=HS256
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=service-role-or-secret
SUPABASE_BUCKET=posts
```

## Run
```bash
uvicorn main:app --reload
```
- Health check: `GET /health`
- Docs: `http://localhost:8000/docs`

## Auth
- Register: `POST /api/auth/register`
- Login: `POST /api/auth/login` (OAuth2 password flow). Use returned bearer token for protected routes.

## Alembic
Initialize DB metadata automatically on startup, or manage migrations:
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Folder Layout
- `core/`: settings, security, JWT helpers
- `db/`: SQLAlchemy Base/session (uses Supabase Postgres via `DATABASE_URL`)
- `db/supabase_client.py`: Supabase client factory
- `models/`: ORM entities
- `schemas/`: Pydantic models
- `repositories/`: CRUD abstractions
- `services/`: business logic (lead scoring, Supabase posts)
- `utils/`: helper utilities (scoring)
- `api/`: route modules

## Posts module (Supabase)
- Exposes `/api/posts` CRUD for company-authenticated users (uses `agency_id` as company id).
- Stores post metadata in Supabase table `posts` (fields: id, title, description, photos[], videos[], company_id, created_at, updated_at).
- Uploads media to Supabase Storage bucket defined by `SUPABASE_BUCKET` (default `posts`).
- Validate image/video types and sizes before upload.
