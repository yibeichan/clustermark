"""
Pytest configuration and fixtures for testing.

Provides test database setup and teardown, isolated sessions for each test.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import models

# Use in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test function.

    Yields a SQLAlchemy Session that is rolled back after the test.
    Uses SQLite in-memory database for speed.

    Note: SQLite doesn't have native UUID type, so we use TEXT and let
    SQLAlchemy handle the conversion (UUID stored as strings).
    SQLite also doesn't support gen_random_uuid(), so we generate UUIDs
    in Python instead.
    """
    # Create engine
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # Enable foreign keys in SQLite (disabled by default)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # For SQLite testing, modify UUID columns and ARRAY columns
    # SQLite doesn't support gen_random_uuid() or ARRAY types
    import uuid as uuid_pkg
    from sqlalchemy.schema import ColumnDefault
    from sqlalchemy import Text, ARRAY

    # Temporarily modify the metadata for SQLite
    for table in Base.metadata.tables.values():
        for column in table.columns:
            # Check if this is a UUID column with gen_random_uuid default
            if column.server_default is not None:
                default_str = str(column.server_default.arg)
                if 'gen_random_uuid' in default_str:
                    # Remove server default and add Python-level default
                    column.server_default = None
                    column.default = ColumnDefault(uuid_pkg.uuid4)

            # Replace ARRAY(Text) with Text for SQLite (store as JSON-like string)
            if isinstance(column.type, ARRAY):
                column.type = Text()

    # Create tables (Gemini MEDIUM: Removed broad except to allow errors to fail clearly)
    # Function-scoped fixtures shouldn't have metadata modification issues between runs
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_episode(test_db):
    """Create a sample Episode for testing."""
    episode = models.Episode(
        name="test_episode",
        total_clusters=2,
        status="pending"
    )
    test_db.add(episode)
    test_db.commit()
    test_db.refresh(episode)
    return episode
