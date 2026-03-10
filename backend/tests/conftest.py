"""
Test configuration and shared fixtures.

Strategy
--------
The app's `database.py` builds a PostgreSQL engine at import time.
We patch `app.core.database.engine` and `SessionLocal` with an
in-memory SQLite engine BEFORE `app.main` is ever imported.
That way `Base.metadata.create_all(bind=engine)` in main.py
picks up the SQLite engine and no real Postgres is needed.

Import order (MUST be preserved):
  1. Set env vars              -prevents None values in the PG URL
  2. Create SQLite engine      - our test engine
  3. Patch app.core.database   - swap in the SQLite engine
  4. Import models             - register them with Base
  5. Create tables             - on the SQLite engine
  6. Import app                - main.py's create_all uses patched engine
"""

import os

#  1. Env vars must be set before any app module is imported 
os.environ.setdefault("POSTGRES_USER",     "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST",     "localhost")
os.environ.setdefault("POSTGRES_PORT",     "5432")
os.environ.setdefault("POSTGRES_DB",       "testdb")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

#  2. In-memory SQLite engine 
# StaticPool forces all sessions to share the same single connection,
# which is required for SQLite :memory: databases to be visible
# across multiple Session objects.
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False)

#  3. Patch the database module BEFORE app.main is imported 
import app.core.database as _db          # noqa: E402  (intentional late import)
_db.engine       = TEST_ENGINE
_db.SessionLocal = TestingSessionLocal

#  4. Import models so SQLAlchemy registers them with Base 
from app.core.database import Base       # noqa: E402
from app.models.fruit import Fruit       # noqa: F401, E402

#  5. Create schema once on the shared SQLite connection 
Base.metadata.create_all(bind=TEST_ENGINE)

#  6. Safe to import the FastAPI app now 
from app.main import app                 # noqa: E402
from app.api.routes import get_db        # noqa: E402


# 
# Seed data — new instances are created per-fixture to avoid
# SQLAlchemy identity-map collisions across tests.
# 
FRUIT_DATA = [
    ("Apple",      "red",    True),
    ("Banana",     "yellow", True),
    ("Grapes",     "purple", False),
    ("Orange",     "orange", True),
    ("Watermelon", "red",    False),
    ("Strawberry", "red",    True),
    ("Peach",      "orange", True),
    ("Pear",       "green",  False),
    ("Pineapple",  "yellow", True),
    ("Mango",      "yellow", True),
    ("Kiwi",       "brown",  False),
]
# in_season=True  → Apple, Banana, Orange, Strawberry, Peach, Pineapple, Mango  (7)
# in_season=False → Grapes, Watermelon, Pear, Kiwi                              (4)
# red fruits      → Apple(T), Watermelon(F), Strawberry(T)                      (3)
# yellow fruits   → Banana(T), Pineapple(T), Mango(T)                           (3)


# 
# Fixtures
# 

@pytest.fixture
def db_session():
    """
    Provides a clean SQLite session.
    Tables are dropped and recreated after each test so state never leaks.
    """
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)
        Base.metadata.create_all(bind=TEST_ENGINE)


@pytest.fixture
def seeded_session(db_session):
    """
    Session pre-loaded with all 11 fruits from FRUIT_DATA.
    Inherits the clean-up behaviour of db_session.
    """
    for name, color, in_season in FRUIT_DATA:
        db_session.add(Fruit(name=name, color=color, in_season=in_season))
    db_session.commit()
    yield db_session


def _make_client(session):
    """
    Return a TestClient that overrides get_db to use *session*.
    Cleans up dependency_overrides after use.
    """
    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session):
    """TestClient backed by an empty database."""
    yield from _make_client(db_session)


@pytest.fixture
def seeded_client(seeded_session):
    """TestClient backed by the pre-seeded database (11 fruits)."""
    yield from _make_client(seeded_session)
