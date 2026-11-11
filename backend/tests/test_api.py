
from fastapi.testclient import TestClient
from main import app
from unittest.mock import MagicMock
from main import get_db
from models import Medication as MedicationDB
from sqlalchemy.exc import IntegrityError


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_get_medications():
    fake_db = MagicMock()

    fake_db.query.return_value.order_by.return_value.all.return_value = []

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/api/medications")

        assert response.status_code == 200
        assert response.json() == []

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_medication_not_found():
    fake_db = MagicMock()
    fake_db.get.return_value = None

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/api/medications/999999")

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Medication not found"
        }

        fake_db.get.assert_called_once_with(
            MedicationDB, 999999
        )

    finally:
        app.dependency_overrides.pop(get_db, None)



def test_get_medication_by_id():
    from datetime import date

    fake_db = MagicMock()

    fake_medication = MedicationDB(
        id=1,
        name="Amoxicillin 500 mg",
        brand="Sample Brand",
        ndc="00000000001",
        expiration_date=date(2027, 6, 30),
        lot_number="TESTLOT001",
        quantity=75,
    )

    fake_db.get.return_value = fake_medication

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get("/api/medications/1")

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == 1
        assert data["name"] == "Amoxicillin 500 mg"
        assert data["quantity"] == 75
        assert data["ndc"] == "00000000001"

        fake_db.get.assert_called_once_with(
            MedicationDB, 1
        )

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_medication():
    fake_db = MagicMock()

    def fake_refresh(medication):
        medication.id = 10

    fake_db.refresh.side_effect = fake_refresh

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
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

        assert response.status_code == 201

        data = response.json()

        assert data["id"] == 10
        assert data["name"] == "Ibuprofen 200 mg"
        assert data["quantity"] == 50
        assert data["ndc"] == "00000000002"

        fake_db.add.assert_called_once()
        fake_db.commit.assert_called_once()
        fake_db.refresh.assert_called_once()

        created_medication = fake_db.add.call_args.args[0]

        assert isinstance(created_medication, MedicationDB)
        assert created_medication.name == "Ibuprofen 200 mg"

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_create_medication_invalid_ndc():
    medication_data = {
        "name": "Ibuprofen 200 mg",
        "brand": "Test Brand",
        "ndc": "12345",
        "expiration_date": "2028-06-30",
        "lot_number": "TESTLOT003",
        "quantity": 50,
    }

    response = client.post(
        "/api/medications",
        json=medication_data,
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        "ndc" in error["loc"]
        for error in errors
    )

def test_create_medication_negative_quantity():
    medication_data = {
        "name": "Ibuprofen 200 mg",
        "brand": "Test Brand",
        "ndc": "00000000003",
        "expiration_date": "2028-06-30",
        "lot_number": "TESTLOT004",
        "quantity": -10,
    }

    response = client.post(
        "/api/medications",
        json=medication_data,
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        "quantity" in error["loc"]
        for error in errors
    )

def test_create_duplicate_medication():
    fake_db = MagicMock()

    fake_db.commit.side_effect = IntegrityError(
        statement="INSERT INTO medications",
        params={},
        orig=Exception("Duplicate NDC and lot number"),
    )

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        medication_data = {
            "name": "Amoxicillin 500 mg",
            "brand": "Sample Brand",
            "ndc": "00000000001",
            "expiration_date": "2027-06-30",
            "lot_number": "TESTLOT001",
            "quantity": 100,
        }

        response = client.post(
            "/api/medications",
            json=medication_data,
        )

        assert response.status_code == 409

        assert "already exists" in response.json()["detail"]

        fake_db.add.assert_called_once()
        fake_db.commit.assert_called_once()
        fake_db.rollback.assert_called_once()

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_update_medication():
    from datetime import date

    fake_db = MagicMock()

    fake_medication = MedicationDB(
        id=1,
        name="Amoxicillin 500 mg",
        brand="Sample Brand",
        ndc="00000000001",
        expiration_date=date(2027, 6, 30),
        lot_number="TESTLOT001",
        quantity=100,
    )

    fake_db.get.return_value = fake_medication

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        updated_data = {
            "name": "Amoxicillin 500 mg",
            "brand": "Sample Brand",
            "ndc": "00000000001",
            "expiration_date": "2027-06-30",
            "lot_number": "TESTLOT001",
            "quantity": 75,
        }

        response = client.put(
            "/api/medications/1",
            json=updated_data,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == 1
        assert data["name"] == "Amoxicillin 500 mg"
        assert data["quantity"] == 75

        assert fake_medication.quantity == 75

        fake_db.get.assert_called_once_with(
            MedicationDB, 1
        )
        fake_db.commit.assert_called_once()
        fake_db.refresh.assert_called_once_with(
            fake_medication
        )

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_update_medication_not_found():
    fake_db = MagicMock()
    fake_db.get.return_value = None

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        updated_data = {
            "name": "Amoxicillin 500 mg",
            "brand": "Sample Brand",
            "ndc": "00000000001",
            "expiration_date": "2027-06-30",
            "lot_number": "TESTLOT001",
            "quantity": 75,
        }

        response = client.put(
            "/api/medications/999999",
            json=updated_data,
        )

        assert response.status_code == 404

        assert response.json() == {
            "detail": "Medication not found"
        }

        fake_db.get.assert_called_once_with(
            MedicationDB, 999999
        )

        fake_db.commit.assert_not_called()
        fake_db.refresh.assert_not_called()

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_update_medication_duplicate_conflict():
    from datetime import date

    fake_db = MagicMock()

    fake_medication = MedicationDB(
        id=1,
        name="Amoxicillin 500 mg",
        brand="Sample Brand",
        ndc="00000000001",
        expiration_date=date(2027, 6, 30),
        lot_number="TESTLOT001",
        quantity=100,
    )

    fake_db.get.return_value = fake_medication

    fake_db.commit.side_effect = IntegrityError(
        statement="UPDATE medications",
        params={},
        orig=Exception("Duplicate NDC and lot number"),
    )

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        updated_data = {
            "name": "Amoxicillin 500 mg",
            "brand": "Sample Brand",
            "ndc": "00000000002",
            "expiration_date": "2027-06-30",
            "lot_number": "TESTLOT002",
            "quantity": 75,
        }

        response = client.put(
            "/api/medications/1",
            json=updated_data,
        )

        assert response.status_code == 409

        assert response.json() == {
            "detail": (
                "Medication update violates "
                "a database constraint"
            )
        }

        fake_db.get.assert_called_once_with(
            MedicationDB, 1
        )

        fake_db.commit.assert_called_once()
        fake_db.rollback.assert_called_once()
        fake_db.refresh.assert_not_called()

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_delete_medication():
    from datetime import date

    fake_db = MagicMock()

    fake_medication = MedicationDB(
        id=10,
        name="Test Medication",
        brand="Test Brand",
        ndc="99999999999",
        expiration_date=date(2028, 12, 31),
        lot_number="DELETE-TEST-001",
        quantity=10,
    )

    fake_db.get.return_value = fake_medication

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.delete("/api/medications/10")

        assert response.status_code == 204
        assert response.content == b""

        fake_db.get.assert_called_once_with(
            MedicationDB, 10
        )

        fake_db.delete.assert_called_once_with(
            fake_medication
        )

        fake_db.commit.assert_called_once()

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_delete_medication_not_found():
    fake_db = MagicMock()
    fake_db.get.return_value = None

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.delete(
            "/api/medications/999999"
        )

        assert response.status_code == 404

        assert response.json() == {
            "detail": "Medication not found"
        }

        fake_db.get.assert_called_once_with(
            MedicationDB, 999999
        )

        fake_db.delete.assert_not_called()
        fake_db.commit.assert_not_called()

    finally:
        app.dependency_overrides.pop(get_db, None)

def test_create_medication_missing_name():
    medication_data = {
        "brand": "Test Brand",
        "ndc": "00000000004",
        "expiration_date": "2028-06-30",
        "lot_number": "TESTLOT005",
        "quantity": 50,
    }

    response = client.post(
        "/api/medications",
        json=medication_data,
    )

    assert response.status_code == 422

    errors = response.json()["detail"]

    assert any(
        "name" in error["loc"]
        for error in errors
    )
