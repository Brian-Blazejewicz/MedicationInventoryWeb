
import pytest

from datetime import datetime, timezone
from types import SimpleNamespace

from main import app, get_current_user


@pytest.fixture
def authenticated_user():
    """Provide a fictional authenticated user for API tests."""

    fake_user = SimpleNamespace(
        id=100,
        email="inventory-test@example.com",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    previous_override = app.dependency_overrides.get(
        get_current_user
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        yield fake_user
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = (
                previous_override
            )
