# User Management API

A simple REST API for managing users, built with FastAPI and SQLite.

## Stack
- **Framework**: FastAPI
- **Database**: SQLite (via sqlite3)
- **Auth**: JWT (PyJWT)
- **Runtime**: Python 3.10+

## Running Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SECRET_KEY | dev-secret-key-change-in-production | JWT signing secret |

## API Endpoints

| Method | Path | Auth Required | Description |
|--------|------|---------------|-------------|
| GET | /health | No | Health check |
| POST | /auth/login | No | Login, returns JWT |
| GET | /users | Yes | List all users |
| GET | /users/{id} | Yes | Get user by ID |
| POST | /users | Yes | Create new user |

## Project Structure
```text
├── main.py        # FastAPI app and route definitions
├── models.py      # Pydantic data models
├── database.py    # SQLite database layer
├── auth.py        # JWT authentication helpers
└── requirements.txt
```
