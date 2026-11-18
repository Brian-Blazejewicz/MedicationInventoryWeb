
from fastapi.testclient import TestClient

from auth import create_access_token
from main import app, get_current_user, get_db
from datetime import datetime, timezone
from types import SimpleNamespace
from datetime import timedelta
import jwt
from auth import SECRET_KEY, ALGORITHM
from security import hash_password

client = TestClient(app)


def test_protected_profile_requires_authentication():
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing authentication credentials."
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_protected_profile_rejects_invalid_token():
    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer invalid-jwt-token"
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing authentication credentials."
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"



def test_protected_profile_returns_authenticated_user():
    fake_user = SimpleNamespace(
        id=123,
        email="test-user@example.com",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        response = client.get("/api/auth/me")

        assert response.status_code == 200

        profile = response.json()

        assert profile["id"] == 123
        assert profile["email"] == "test-user@example.com"
        assert profile["is_active"] is True
        assert "hashed_password" not in profile
        assert "password" not in profile

    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_valid_jwt_authenticates_user():
    fake_user = SimpleNamespace(
        id=456,
        email="jwt-test@example.com",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    class FakeDatabase:
        def get(self, model, user_id):
            if user_id == fake_user.id:
                return fake_user
            return None

    def override_get_db():
        yield FakeDatabase()

    token = create_access_token(user_id=fake_user.id)

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        profile = response.json()

        assert profile["id"] == 456
        assert profile["email"] == "jwt-test@example.com"
        assert profile["is_active"] is True
        assert "hashed_password" not in profile
        assert "password" not in profile

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_protected_profile_rejects_expired_token():
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    expired_token = jwt.encode(
        {
            "sub": "456",
            "exp": expired_time,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing authentication credentials."
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"

def test_protected_profile_rejects_nonexistent_user():
    class FakeDatabase:
        def get(self, model, user_id):
            return None

    def override_get_db():
        yield FakeDatabase()

    token = create_access_token(user_id=999999)

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid or missing authentication credentials."
        }
        assert response.headers["WWW-Authenticate"] == "Bearer"

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_protected_profile_rejects_inactive_user():
    fake_user = SimpleNamespace(
        id=789,
        email="inactive-test@example.com",
        is_active=False,
        created_at=datetime.now(timezone.utc),
    )

    class FakeDatabase:
        def get(self, model, user_id):
            if user_id == fake_user.id:
                return fake_user
            return None

    def override_get_db():
        yield FakeDatabase()

    token = create_access_token(user_id=fake_user.id)

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/api/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid or missing authentication credentials."
        }
        assert response.headers["WWW-Authenticate"] == "Bearer"

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_registration_rejects_duplicate_email():
    fake_existing_user = SimpleNamespace(
        id=1,
        email="existing@example.com",
        is_active=True,
    )

    class FakeDatabase:
        def scalar(self, statement):
            return fake_existing_user

    def override_get_db():
        yield FakeDatabase()

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/auth/register",
            json={
                "email": "existing@example.com",
                "password": "TestPassword123!",
            },
        )

        assert response.status_code == 409
        assert response.json() == {
            "detail": "An account with this email already exists."
        }

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_login_rejects_incorrect_password():
    fake_user = SimpleNamespace(
        id=321,
        email="login-test@example.com",
        hashed_password=hash_password("CorrectPassword123!"),
        is_active=True,
    )

    class FakeDatabase:
        def scalar(self, statement):
            return fake_user

    def override_get_db():
        yield FakeDatabase()

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login-test@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid email or password."
        }
        assert response.headers["WWW-Authenticate"] == "Bearer"

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_registration_and_login_success():
    stored_users = {}

    class FakeDatabase:
        def scalar(self, statement):
            return stored_users.get("user")

        def add(self, user):
            user.id = 1001
            user.is_active = True
            user.created_at = datetime.now(timezone.utc)
            stored_users["user"] = user

        def commit(self):
            pass

        def refresh(self, user):
            pass

    def override_get_db():
        yield FakeDatabase()

    app.dependency_overrides[get_db] = override_get_db

    try:
        registration_response = client.post(
            "/api/auth/register",
            json={
                "email": "new-test@example.com",
                "password": "TestPassword123!",
            },
        )

        assert registration_response.status_code == 201

        registration_data = registration_response.json()

        assert registration_data["email"] == "new-test@example.com"
        assert "hashed_password" not in registration_data
        assert "password" not in registration_data

        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "new-test@example.com",
                "password": "TestPassword123!",
            },
        )

        assert login_response.status_code == 200

        login_data = login_response.json()

        assert login_data["token_type"] == "bearer"
        assert bool(login_data["access_token"])

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_medications_require_authentication():
    """Unauthenticated users cannot access medication inventory."""

    response = client.get("/api/medications")

    assert response.status_code == 401

def test_create_medication_requires_authentication():
    """Unauthenticated users cannot create medications."""

    medication_data = {
        "name": "Ibuprofen 200 mg",
        "brand": "Test Brand",
        "ndc": "00000000002",
        "expiration_date": "2028-06-30",
        "lot_number": "TESTLOT002",
        "quantity": 50,
    }

    response = client.post(
        "/api/medications",
        json=medication_data,
    )

    assert response.status_code == 401

def test_get_medication_by_id_requires_authentication():
    """Unauthenticated users cannot retrieve medication records."""

    response = client.get("/api/medications/1")

    assert response.status_code == 401

def test_update_medication_requires_authentication():
    """Unauthenticated users cannot update medications."""

    updated_data = {
        "name": "Ibuprofen 200 mg",
        "brand": "Test Brand",
        "ndc": "00000000002",
        "expiration_date": "2028-06-30",
        "lot_number": "TESTLOT002",
        "quantity": 50,
    }

    response = client.put(
        "/api/medications/1",
        json=updated_data,
    )

    assert response.status_code == 401

def test_delete_medication_requires_authentication():
    """Unauthenticated users cannot delete medications."""

    response = client.delete("/api/medications/1")

    assert response.status_code == 401

def test_transaction_history_requires_authentication():
    """Unauthenticated users cannot view inventory history."""

    response = client.get(
        "/api/medications/1/transactions"
    )

    assert response.status_code == 401

def test_stock_in_requires_authentication():
    """Unauthenticated users cannot add medication stock."""

    response = client.post(
        "/api/medications/1/stock-in",
        json={"quantity": 25},
    )

    assert response.status_code == 401

def test_stock_out_requires_authentication():
    """Unauthenticated users cannot remove medication stock."""

    response = client.post(
        "/api/medications/1/stock-out",
        json={"quantity": 10},
    )

    assert response.status_code == 401
