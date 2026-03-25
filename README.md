# Fruit App

A full-stack web application for browsing, filtering, and searching fruits.

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | FastAPI, SQLAlchemy(ORM), PostgreSQL|
| Frontend  | React 18, Vite, Axios               |
| Testing   | Pytest                              |
| Deploy    | Docker, Docker Compose              |

---

## Project Structure

```
fruit_app/
├── .env                        # Environment variables
├── docker-compose.yml          # Multi-container orchestration
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── api/routes.py       # API endpoint definitions
│   │   ├── core/database.py    # Database connection setup
│   │   ├── models/fruit.py     # SQLAlchemy ORM model
│   │   ├── services/fruit_service.py  # Business logic & fuzzy filtering
│   │   └── scripts/seed_db.py  # DB seeding script
│   ├── data/fruitList.json     # Seed data
│   ├── tests/
│   │   ├── conftest.py         # Fixtures
│   │   ├── test_api.py         # API integration tests
│   │   └── test_service.py     # Service unit tests
│   ├── Dockerfile
│   └── pyproject.toml
└── frontend/
    ├── src/
    │   ├── main.jsx            # React entry point
    │   └── App.jsx             # Main component (filters, pagination, display)
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── Dockerfile
```

---

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

### Run with Docker Compose

```bash
# Clone and enter the project
cd fruit_app

# Start all services (database, backend, frontend)
docker-compose up --build # or docker compose up --build

# Seed the database with sample fruits
docker-compose exec backend python app/scripts/seed_db.py # or docker compose exec backend python app/scripts/seed_db.py
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173      |
| Backend  | http://localhost:8000      |
| API Docs | http://localhost:8000/docs |

To stop:

```bash
docker-compose down # or docker compose down

```

To stop and remove the database volume:

```bash
docker-compose down -v # or docker compose down -v
```

---

## API Reference

### `GET /fruit`

Returns list of fruits, with optional filtering.

**Query Parameters**

| Parameter   | Type    | Default | Description                              |
|-------------|---------|---------|------------------------------------------|
| `name`      | string  | —       | Filter by name (fuzzy match supported)   |
| `color`     | string  | —       | Filter by color (fuzzy match supported)  |
| `in_season` | boolean | —       | Filter by season 

**Example Request**

```bash
curl "http://localhost:8000/fruit?color=red&in_season=true&page=1&page_size=5"
```

**Example Response**

```json
{
  "total": 2,
  "page": 1,
  "page_size": 5,
  "items": [
    { "id": 1, "name": "Apple", "color": "red", "in_season": true },
    { "id": 5, "name": "Strawberry", "color": "red", "in_season": true }
  ]
}
```

## Running Tests

Tests use an in-memory SQLite database — no running services required.

```bash
cd backend

# Install dependencies (using uv)
uv sync

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=app
```

**Test coverage includes:**
- API integration tests: response structure, all filters, pagination, input validation
- Service unit tests: fuzzy matching behavior, filter combinations, pagination correctness

---

## Configuration

Environment variables are defined in `.env` at the project root.

---
