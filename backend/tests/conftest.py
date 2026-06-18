"""
Pytest fixtures for the TradeAI test suite.
Designed to be robust and independent of external services in CI.
"""
import asyncio
import hashlib
import uuid
from decimal import Decimal
from typing import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app

# ─── Test Database (in-memory SQLite) ────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:?cache=shared"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── Simple password helpers (no bcrypt dependency) ──────────────────────────
def _simple_hash(password: str) -> str:
    """SHA-256 hash used ONLY in tests to avoid bcrypt dependency issues."""
    return "sha256:" + hashlib.sha256(password.encode()).hexdigest()


def _simple_verify(plain: str, hashed: str) -> bool:
    return hashed == _simple_hash(plain)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_setup():
    """Create schema once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(db_setup) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional test session that rolls back after each test."""
    async with test_engine.connect() as conn:
        await conn.begin()
        async_session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield async_session
        finally:
            await async_session.close()
            await conn.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client backed by the test database."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Patch password functions to use simple SHA-256 (avoids bcrypt issues)
    with patch("app.core.security.get_password_hash", side_effect=_simple_hash), \
         patch("app.core.security.verify_password", side_effect=_simple_verify), \
         patch("app.auth.service.get_password_hash", side_effect=_simple_hash), \
         patch("app.auth.service.verify_password", side_effect=_simple_verify):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Create a test user directly in DB (bypasses bcrypt)."""
    from app.auth.models import User

    user = User(
        id=uuid.uuid4(),
        email="test@tradeai.com",
        username="testtrader",
        hashed_password=_simple_hash("TestPass123"),
        full_name="Test Trader",
        balance=Decimal("100000.00"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Return authorization headers for the test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def patch_yfinance(monkeypatch):
    """Mock yfinance so tests never make real HTTP calls."""
    import pandas as pd

    class MockFastInfo:
        last_price = 150.0
        previous_close = 148.0
        market_cap = 2_000_000_000
        shares_outstanding = 1_000_000

    class MockTicker:
        def __init__(self, symbol):
            self.symbol = symbol
            self.fast_info = MockFastInfo()
            self.info = {
                "regularMarketPrice": 150.0,
                "regularMarketPreviousClose": 148.0,
                "volume": 1_000_000,
                "marketCap": 2_000_000_000,
                "shortName": symbol,
                "longName": f"{symbol} Inc.",
                "sector": "Technology",
            }

        def history(self, *args, **kwargs):
            return pd.DataFrame({
                "Open":   [148.0, 149.0, 150.0],
                "High":   [151.0, 152.0, 153.0],
                "Low":    [147.0, 148.0, 149.0],
                "Close":  [149.0, 150.0, 151.0],
                "Volume": [1_000_000, 1_100_000, 1_200_000],
            })

    monkeypatch.setattr("yfinance.Ticker", MockTicker)
