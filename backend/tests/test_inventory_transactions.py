
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from main import app, get_db
from models import (
    Medication as MedicationDB,
    InventoryTransaction as InventoryTransactionDB,
)


client = TestClient(app)


def test_stock_in_success():
    # Create a fictional medication in memory.
    medication = MedicationDB(
        id=1,
        name="Stock IN Test Medication",
        brand="Test Brand",
        ndc="99999999981",
        expiration_date=date(2028, 12, 31),
        lot_number="STOCKIN001",
        quantity=100,
    )

    fake_db = MagicMock()

    # Simulate the result of SELECT ... FOR UPDATE.
    fake_db.execute.return_value.scalar_one_or_none.return_value = medication

    # Simulate PostgreSQL generating transaction values.
    def fake_refresh(transaction):
        transaction.id = 10
        transaction.timestamp = datetime(
            2026, 11, 10, 21, 30, tzinfo=timezone.utc
        )

    fake_db.refresh.side_effect = fake_refresh

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/medications/1/stock-in",
            json={"quantity": 25},
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"] == 10
        assert data["medication_id"] == 1
        assert data["action"] == "IN"
        assert data["quantity"] == 25

        # Verify the medication quantity increased.
        assert medication.quantity == 125

        # Verify the transaction was created correctly.
        fake_db.add.assert_called_once()

        transaction = fake_db.add.call_args.args[0]

        assert isinstance(
            transaction,
            InventoryTransactionDB,
        )
        assert transaction.medication_id == 1
        assert transaction.action == "IN"
        assert transaction.quantity == 25

        # Verify the database transaction was committed.
        fake_db.commit.assert_called_once()
        fake_db.rollback.assert_not_called()

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_stock_out_success():
    # Create a fictional medication with 125 units.
    medication = MedicationDB(
        id=1,
        name="Stock OUT Test Medication",
        brand="Test Brand",
        ndc="99999999982",
        expiration_date=date(2028, 12, 31),
        lot_number="STOCKOUT001",
        quantity=125,
    )

    fake_db = MagicMock()

    # Simulate the locked medication query.
    fake_db.execute.return_value.scalar_one_or_none.return_value = medication

    # Simulate database-generated transaction fields.
    def fake_refresh(transaction):
        transaction.id = 11
        transaction.timestamp = datetime(
            2026, 11, 10, 22, 0, tzinfo=timezone.utc
        )

    fake_db.refresh.side_effect = fake_refresh

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/medications/1/stock-out",
            json={"quantity": 20},
        )

        # Verify successful HTTP response.
        assert response.status_code == 201

        data = response.json()

        assert data["id"] == 11
        assert data["medication_id"] == 1
        assert data["action"] == "OUT"
        assert data["quantity"] == 20

        # Verify that stock decreased correctly.
        assert medication.quantity == 105

        # Verify that an OUT transaction was created.
        fake_db.add.assert_called_once()

        transaction = fake_db.add.call_args.args[0]

        assert isinstance(
            transaction,
            InventoryTransactionDB,
        )
        assert transaction.medication_id == 1
        assert transaction.action == "OUT"
        assert transaction.quantity == 20

        # Verify the transaction was committed.
        fake_db.commit.assert_called_once()
        fake_db.rollback.assert_not_called()

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_stock_out_insufficient_inventory():
    # Create a fictional medication with only 10 units.
    medication = MedicationDB(
        id=1,
        name="Insufficient Stock Test Medication",
        brand="Test Brand",
        ndc="99999999983",
        expiration_date=date(2028, 12, 31),
        lot_number="LOWSTOCK001",
        quantity=10,
    )

    fake_db = MagicMock()

    # Simulate the database returning the medication.
    fake_db.execute.return_value.scalar_one_or_none.return_value = medication

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Attempt to remove 25 units when only 10 exist.
        response = client.post(
            "/api/medications/1/stock-out",
            json={"quantity": 25},
        )

        # The API should reject the operation.
        assert response.status_code == 409

        assert response.json() == {
            "detail": "Insufficient inventory. Available quantity: 10"
        }

        # The medication quantity must remain unchanged.
        assert medication.quantity == 10

        # No inventory transaction should be created.
        fake_db.add.assert_not_called()

        # No changes should be committed.
        fake_db.commit.assert_not_called()

        # The failed operation should roll back the session.
        fake_db.rollback.assert_called_once()

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_stock_in_zero_quantity():
    response = client.post(
        "/api/medications/1/stock-in",
        json={"quantity": 0},
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        "quantity" in error["loc"]
        for error in errors
    )


def test_stock_out_negative_quantity():
    response = client.post(
        "/api/medications/1/stock-out",
        json={"quantity": -5},
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        "quantity" in error["loc"]
        for error in errors
    )

def test_stock_in_medication_not_found():
    fake_db = MagicMock()

    # Simulate a database query that finds no medication.
    fake_db.execute.return_value.scalar_one_or_none.return_value = None

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/medications/999999/stock-in",
            json={"quantity": 10},
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Medication not found"
        }

        fake_db.add.assert_not_called()
        fake_db.commit.assert_not_called()
        fake_db.rollback.assert_called_once()

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_stock_out_medication_not_found():
    fake_db = MagicMock()

    # Simulate a database query that finds no medication.
    fake_db.execute.return_value.scalar_one_or_none.return_value = None

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/api/medications/999999/stock-out",
            json={"quantity": 10},
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Medication not found"
        }

        fake_db.add.assert_not_called()
        fake_db.commit.assert_not_called()
        fake_db.rollback.assert_called_once()

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_medication_transaction_history():
    # Create a fictional medication.
    medication = MedicationDB(
        id=1,
        name="Transaction History Test",
        brand="Test Brand",
        ndc="99999999984",
        expiration_date=date(2028, 12, 31),
        lot_number="HISTORY001",
        quantity=105,
    )

    # Create two fictional inventory transactions.
    stock_in_transaction = InventoryTransactionDB(
        id=1,
        medication_id=1,
        action="IN",
        quantity=25,
        timestamp=datetime(
            2026, 11, 10, 20, 0, tzinfo=timezone.utc
        ),
    )

    stock_out_transaction = InventoryTransactionDB(
        id=2,
        medication_id=1,
        action="OUT",
        quantity=20,
        timestamp=datetime(
            2026, 11, 10, 21, 0, tzinfo=timezone.utc
        ),
    )

    fake_db = MagicMock()
    fake_db.get.return_value = medication

    # Simulate the database returning newest transactions first.
    fake_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        stock_out_transaction,
        stock_in_transaction,
    ]

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/api/medications/1/transactions"
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2

        # Newest transaction should appear first.
        assert data[0]["action"] == "OUT"
        assert data[0]["quantity"] == 20
        assert data[0]["medication_id"] == 1

        assert data[1]["action"] == "IN"
        assert data[1]["quantity"] == 25
        assert data[1]["medication_id"] == 1

        fake_db.get.assert_called_once_with(
            MedicationDB, 1
        )

        fake_db.query.assert_called_once_with(
            InventoryTransactionDB
        )

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_stock_in_database_failure_rolls_back():
    # Create a fictional medication.
    medication = MedicationDB(
        id=1,
        name="Rollback Test Medication",
        brand="Test Brand",
        ndc="99999999985",
        expiration_date=date(2028, 12, 31),
        lot_number="ROLLBACK001",
        quantity=100,
    )

    fake_db = MagicMock()

    # Simulate PostgreSQL finding and locking the medication.
    fake_db.execute.return_value.scalar_one_or_none.return_value = medication

    # Simulate a database error when committing.
    fake_db.commit.side_effect = RuntimeError(
        "Simulated database failure"
    )

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Disable exception propagation so we can inspect
        # the HTTP 500 response from FastAPI.
        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as test_client:
            response = test_client.post(
                "/api/medications/1/stock-in",
                json={"quantity": 25},
            )

        # An unexpected database error should return HTTP 500.
        assert response.status_code == 500

        # The endpoint attempted to save the changes.
        fake_db.commit.assert_called_once()

        # The endpoint must roll back the failed transaction.
        fake_db.rollback.assert_called_once()

        # The inventory transaction was prepared.
        fake_db.add.assert_called_once()

        transaction = fake_db.add.call_args.args[0]

        assert isinstance(
            transaction,
            InventoryTransactionDB,
        )
        assert transaction.action == "IN"
        assert transaction.quantity == 25

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_stock_out_database_failure_rolls_back():
    # Create a fictional medication with 100 units.
    medication = MedicationDB(
        id=1,
        name="Stock OUT Rollback Test",
        brand="Test Brand",
        ndc="99999999986",
        expiration_date=date(2028, 12, 31),
        lot_number="OUTROLLBACK001",
        quantity=100,
    )

    fake_db = MagicMock()

    # Simulate finding and locking the medication.
    fake_db.execute.return_value.scalar_one_or_none.return_value = medication

    # Simulate a database failure during commit.
    fake_db.commit.side_effect = RuntimeError(
        "Simulated Stock OUT database failure"
    )

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Prevent TestClient from re-raising the simulated error.
        with TestClient(
            app,
            raise_server_exceptions=False,
        ) as test_client:
            response = test_client.post(
                "/api/medications/1/stock-out",
                json={"quantity": 25},
            )

        # The failed operation should return HTTP 500.
        assert response.status_code == 500

        # The endpoint attempted to save the changes.
        fake_db.commit.assert_called_once()

        # The failed transaction must be rolled back.
        fake_db.rollback.assert_called_once()

        # Verify an OUT transaction was prepared.
        fake_db.add.assert_called_once()

        transaction = fake_db.add.call_args.args[0]

        assert isinstance(
            transaction,
            InventoryTransactionDB,
        )
        assert transaction.medication_id == 1
        assert transaction.action == "OUT"
        assert transaction.quantity == 25

        # The in-memory medication object was modified
        # before the simulated commit failure.
        assert medication.quantity == 75

    finally:
        app.dependency_overrides.pop(get_db, None)
