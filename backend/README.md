# Backend API Service

FastAPI-based backend service for the Smart Triage Kiosk System.

## Features

- FastAPI with automatic OpenAPI documentation
- PostgreSQL with SQLAlchemy ORM
- Redis for caching and sessions
- JWT authentication with role-based access
- Celery for background tasks
- FHIR-compliant data models
- Comprehensive logging and monitoring
- HIPAA-compliant security measures

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
ENVIRONMENT=development
```

## Project Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Core configuration
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── ml/            # ML integration
│   ├── devices/       # Device integration
│   └── utils/         # Utilities
├── alembic/           # Database migrations
├── tests/             # Test suite
├── Dockerfile         # Docker configuration
└── requirements.txt   # Dependencies
```
