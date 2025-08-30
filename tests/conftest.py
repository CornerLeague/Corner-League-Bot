"""Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for all test modules.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from libs.common.database import DatabaseManager
from libs.common.config import Settings, DatabaseSettings
from apps.api.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with in-memory database."""
    settings = Settings()
    settings.database = DatabaseSettings(
        url="sqlite+aiosqlite:///:memory:",
        echo=False,
        pool_size=1,
        max_overflow=0
    )
    settings.testing = True
    return settings


@pytest.fixture
async def test_db_engine(test_settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.database.url,
        echo=test_settings.database.echo
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_db_manager() -> MagicMock:
    """Create mock database manager."""
    db_manager = MagicMock(spec=DatabaseManager)
    
    # Mock session context manager
    mock_session = AsyncMock(spec=AsyncSession)
    db_manager.session.return_value.__aenter__.return_value = mock_session
    db_manager.session.return_value.__aexit__.return_value = None
    
    # Mock transaction context manager
    db_manager.transaction.return_value.__aenter__.return_value = mock_session
    db_manager.transaction.return_value.__aexit__.return_value = None
    
    return db_manager


@pytest.fixture
def mock_async_session() -> AsyncMock:
    """Create mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock common session methods
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.flush = AsyncMock()
    
    return session


@pytest.fixture
def test_client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_clerk_user():
    """Mock Clerk user data."""
    return {
        "sub": "user_test123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "roles": ["user"],
        "iat": 1640995200,  # 2022-01-01
        "exp": 1640998800,  # 2022-01-01 + 1 hour
        "iss": "https://test.clerk.accounts.dev",
        "aud": "test-audience"
    }


@pytest.fixture
def mock_admin_user():
    """Mock Clerk admin user data."""
    return {
        "sub": "user_admin123",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "username": "adminuser",
        "roles": ["admin", "user"],
        "iat": 1640995200,
        "exp": 1640998800,
        "iss": "https://test.clerk.accounts.dev",
        "aud": "test-audience"
    }


@pytest.fixture
def sample_sports_data():
    """Sample sports data for testing."""
    return [
        {
            "id": 1,
            "name": "baseball",
            "display_name": "Baseball",
            "description": "America's pastime",
            "is_active": True
        },
        {
            "id": 2,
            "name": "basketball",
            "display_name": "Basketball",
            "description": "Fast-paced indoor sport",
            "is_active": True
        },
        {
            "id": 3,
            "name": "football",
            "display_name": "Football",
            "description": "American football",
            "is_active": True
        }
    ]


@pytest.fixture
def sample_teams_data():
    """Sample teams data for testing."""
    return [
        {
            "id": 1,
            "name": "Los Angeles Dodgers",
            "sport_id": 1,
            "city": "Los Angeles",
            "state": "CA",
            "league": "MLB",
            "division": "NL West",
            "is_active": True
        },
        {
            "id": 2,
            "name": "New York Yankees",
            "sport_id": 1,
            "city": "New York",
            "state": "NY",
            "league": "MLB",
            "division": "AL East",
            "is_active": True
        },
        {
            "id": 3,
            "name": "Los Angeles Lakers",
            "sport_id": 2,
            "city": "Los Angeles",
            "state": "CA",
            "league": "NBA",
            "division": "Western Conference",
            "is_active": True
        }
    ]


@pytest.fixture
def sample_user_preferences():
    """Sample user preferences data for testing."""
    return {
        "user_id": "user_test123",
        "sport_rankings": [
            {"sport_id": 1, "rank": 1},
            {"sport_id": 2, "rank": 2},
            {"sport_id": 3, "rank": 3}
        ],
        "team_preferences": [1, 2, 3],
        "questionnaire_status": "completed"
    }


# Pytest markers for different test types
pytestmark = [
    pytest.mark.asyncio,  # All tests are async by default
]


# Custom pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database related"
    )


# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add markers based on test name
        if "auth" in item.name.lower():
            item.add_marker(pytest.mark.auth)
        if "database" in item.name.lower() or "db" in item.name.lower():
            item.add_marker(pytest.mark.database)
        if "slow" in item.name.lower() or "concurrent" in item.name.lower():
            item.add_marker(pytest.mark.slow)