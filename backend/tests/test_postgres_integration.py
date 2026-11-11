
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from main import app, get_db
from models import (
    Medication as MedicationDB,
    InventoryTransaction as InventoryTransactionDB,
)
from tests.test_database import create_test_engine


def test_postgres_stock_in():
    # Connect only to the dedicated PostgreSQL test database.
    engine = create_test_engine()

    medication_id = None

    try:
        # Create fictional test data with a unique NDC/lot pair.
        test_medication = MedicationDB(
            name="PostgreSQL Stock IN Test",
            brand="Test Brand",
            ndc="99999999987",
            expiration_date=date(2028, 12, 31),
            lot_number=f"PGTEST-{uuid.uuid4().hex[:12]}",
            quantity=100,
        )

        # Insert the medication using a real database session.
        with Session(engine) as db:
            db.add(test_medication)
            db.commit()
            db.refresh(test_medication)
            medication_id = test_medication.id

        # Override FastAPI's normal database dependency.
        # This ensures the endpoint uses the test database.
        def override_get_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/medications/{medication_id}/stock-in",
                    json={"quantity": 25},
                )

            assert response.status_code == 201

            data = response.json()

            assert data["medication_id"] == medication_id
            assert data["action"] == "IN"
            assert data["quantity"] == 25
            assert data["id"] > 0
            assert data["timestamp"]

        finally:
            app.dependency_overrides.pop(get_db, None)

        # Open a NEW session to verify committed PostgreSQL data.
        with Session(engine) as db:
            saved_medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert saved_medication is not None
            assert saved_medication.quantity == 125

            transactions = db.scalars(
                select(InventoryTransactionDB).where(
                    InventoryTransactionDB.medication_id
                    == medication_id
                )
            ).all()

            assert len(transactions) == 1
            assert transactions[0].action == "IN"
            assert transactions[0].quantity == 25

    finally:
        # Clean up only the records created by this test.
        if medication_id is not None:
            with Session(engine) as db:
                try:
                    transactions = db.scalars(
                        select(InventoryTransactionDB).where(
                            InventoryTransactionDB.medication_id
                            == medication_id
                        )
                    ).all()

                    for transaction in transactions:
                        db.delete(transaction)

                    medication = db.get(
                        MedicationDB,
                        medication_id,
                    )

                    if medication is not None:
                        db.delete(medication)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise

        engine.dispose()

def test_postgres_stock_out():
    # Connect only to the dedicated PostgreSQL test database.
    engine = create_test_engine()

    medication_id = None

    try:
        # Create a fictional medication with 125 units.
        test_medication = MedicationDB(
            name="PostgreSQL Stock OUT Test",
            brand="Test Brand",
            ndc="99999999988",
            expiration_date=date(2028, 12, 31),
            lot_number=f"PGOUT-{uuid.uuid4().hex[:12]}",
            quantity=125,
        )

        # Insert the medication into the test database.
        with Session(engine) as db:
            db.add(test_medication)
            db.commit()
            db.refresh(test_medication)
            medication_id = test_medication.id

        # Force the FastAPI endpoint to use the test database.
        def override_get_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/medications/{medication_id}/stock-out",
                    json={"quantity": 20},
                )

            assert response.status_code == 201

            data = response.json()

            assert data["medication_id"] == medication_id
            assert data["action"] == "OUT"
            assert data["quantity"] == 20
            assert data["id"] > 0
            assert data["timestamp"]

        finally:
            app.dependency_overrides.pop(get_db, None)

        # Verify committed data using a new database session.
        with Session(engine) as db:
            saved_medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert saved_medication is not None
            assert saved_medication.quantity == 105

            transactions = db.scalars(
                select(InventoryTransactionDB).where(
                    InventoryTransactionDB.medication_id
                    == medication_id
                )
            ).all()

            assert len(transactions) == 1
            assert transactions[0].action == "OUT"
            assert transactions[0].quantity == 20

    finally:
        # Remove only records created by this test.
        if medication_id is not None:
            with Session(engine) as db:
                try:
                    transactions = db.scalars(
                        select(InventoryTransactionDB).where(
                            InventoryTransactionDB.medication_id
                            == medication_id
                        )
                    ).all()

                    for transaction in transactions:
                        db.delete(transaction)

                    medication = db.get(
                        MedicationDB,
                        medication_id,
                    )

                    if medication is not None:
                        db.delete(medication)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise

        engine.dispose()

def test_postgres_stock_out_insufficient_inventory():
    # Connect only to the dedicated test database.
    engine = create_test_engine()

    medication_id = None

    try:
        # Create a fictional medication with only 10 units.
        test_medication = MedicationDB(
            name="PostgreSQL Insufficient Stock Test",
            brand="Test Brand",
            ndc="99999999989",
            expiration_date=date(2028, 12, 31),
            lot_number=f"PGLOW-{uuid.uuid4().hex[:12]}",
            quantity=10,
        )

        # Insert the medication into PostgreSQL.
        with Session(engine) as db:
            db.add(test_medication)
            db.commit()
            db.refresh(test_medication)
            medication_id = test_medication.id

        # Override FastAPI's database dependency.
        def override_get_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/medications/{medication_id}/stock-out",
                    json={"quantity": 25},
                )

            # PostgreSQL-backed API must reject the request.
            assert response.status_code == 409

            assert response.json() == {
                "detail": (
                    "Insufficient inventory. "
                    "Available quantity: 10"
                )
            }

        finally:
            app.dependency_overrides.pop(get_db, None)

        # Verify actual PostgreSQL data remains unchanged.
        with Session(engine) as db:
            saved_medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert saved_medication is not None
            assert saved_medication.quantity == 10

            transactions = db.scalars(
                select(InventoryTransactionDB).where(
                    InventoryTransactionDB.medication_id
                    == medication_id
                )
            ).all()

            # No OUT transaction should have been saved.
            assert len(transactions) == 0

    finally:
        # Clean up only the fictional medication created here.
        if medication_id is not None:
            with Session(engine) as db:
                try:
                    transactions = db.scalars(
                        select(InventoryTransactionDB).where(
                            InventoryTransactionDB.medication_id
                            == medication_id
                        )
                    ).all()

                    for transaction in transactions:
                        db.delete(transaction)

                    medication = db.get(
                        MedicationDB,
                        medication_id,
                    )

                    if medication is not None:
                        db.delete(medication)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise

        engine.dispose()

def test_postgres_transaction_rollback():
    # Connect only to the dedicated PostgreSQL test database.
    engine = create_test_engine()

    medication_id = None

    try:
        # Create a fictional medication with 100 units.
        test_medication = MedicationDB(
            name="PostgreSQL Rollback Test",
            brand="Test Brand",
            ndc="99999999990",
            expiration_date=date(2028, 12, 31),
            lot_number=f"PGROLL-{uuid.uuid4().hex[:12]}",
            quantity=100,
        )

        # Save the initial medication record.
        with Session(engine) as db:
            db.add(test_medication)
            db.commit()
            db.refresh(test_medication)
            medication_id = test_medication.id

        # Begin a real PostgreSQL transaction.
        with Session(engine) as db:
            medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert medication is not None
            assert medication.quantity == 100

            # Simulate a Stock IN operation.
            medication.quantity += 25

            transaction = InventoryTransactionDB(
                medication_id=medication_id,
                action="IN",
                quantity=25,
            )

            db.add(transaction)

            # Send pending changes to PostgreSQL,
            # but do not commit them.
            db.flush()

            assert medication.quantity == 125
            assert transaction.id is not None

            # Simulate an application failure by rolling back.
            db.rollback()

        # Use a new session to inspect committed database data.
        with Session(engine) as db:
            saved_medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert saved_medication is not None

            # The original quantity must remain unchanged.
            assert saved_medication.quantity == 100

            transactions = db.scalars(
                select(InventoryTransactionDB).where(
                    InventoryTransactionDB.medication_id
                    == medication_id
                )
            ).all()

            # The rolled-back transaction must not exist.
            assert len(transactions) == 0

    finally:
        # Clean up the fictional medication.
        if medication_id is not None:
            with Session(engine) as db:
                try:
                    transactions = db.scalars(
                        select(InventoryTransactionDB).where(
                            InventoryTransactionDB.medication_id
                            == medication_id
                        )
                    ).all()

                    for transaction in transactions:
                        db.delete(transaction)

                    medication = db.get(
                        MedicationDB,
                        medication_id,
                    )

                    if medication is not None:
                        db.delete(medication)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise

        engine.dispose()

def test_postgres_transaction_history():
    # Connect only to the dedicated PostgreSQL test database.
    engine = create_test_engine()
    medication_id = None

    try:
        # Create a fictional medication with 100 units.
        test_medication = MedicationDB(
            name="PostgreSQL Transaction History Test",
            brand="Test Brand",
            ndc="99999999991",
            expiration_date=date(2028, 12, 31),
            lot_number=f"PGHISTORY-{uuid.uuid4().hex[:12]}",
            quantity=100,
        )

        with Session(engine) as db:
            db.add(test_medication)
            db.commit()
            db.refresh(test_medication)
            medication_id = test_medication.id

        # Redirect API database operations to the test database.
        def override_get_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # First transaction: receive 25 units.
                stock_in_response = client.post(
                    f"/api/medications/{medication_id}/stock-in",
                    json={"quantity": 25},
                )

                assert stock_in_response.status_code == 201

                # Second transaction: remove 20 units.
                stock_out_response = client.post(
                    f"/api/medications/{medication_id}/stock-out",
                    json={"quantity": 20},
                )

                assert stock_out_response.status_code == 201

                # Retrieve the transaction history.
                history_response = client.get(
                    f"/api/medications/{medication_id}/transactions"
                )

            assert history_response.status_code == 200

            history = history_response.json()

            assert len(history) == 2

            # Newest transaction should appear first.
            assert history[0]["action"] == "OUT"
            assert history[0]["quantity"] == 20
            assert history[0]["medication_id"] == medication_id

            assert history[1]["action"] == "IN"
            assert history[1]["quantity"] == 25
            assert history[1]["medication_id"] == medication_id

            # Verify both records have generated IDs and timestamps.
            assert history[0]["id"] > 0
            assert history[1]["id"] > 0
            assert history[0]["timestamp"]
            assert history[1]["timestamp"]

            # Verify the newest-first ordering is consistent
            # with the API's timestamp/id ordering.
            assert history[0]["timestamp"] >= history[1]["timestamp"]

        finally:
            app.dependency_overrides.pop(get_db, None)

        # Verify the final quantity in PostgreSQL.
        with Session(engine) as db:
            saved_medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert saved_medication is not None
            assert saved_medication.quantity == 105

            transactions = db.scalars(
                select(InventoryTransactionDB).where(
                    InventoryTransactionDB.medication_id
                    == medication_id
                )
            ).all()

            assert len(transactions) == 2

    finally:
        # Delete only records created by this test.
        if medication_id is not None:
            with Session(engine) as db:
                try:
                    transactions = db.scalars(
                        select(InventoryTransactionDB).where(
                            InventoryTransactionDB.medication_id
                            == medication_id
                        )
                    ).all()

                    for transaction in transactions:
                        db.delete(transaction)

                    medication = db.get(
                        MedicationDB,
                        medication_id,
                    )

                    if medication is not None:
                        db.delete(medication)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise

        engine.dispose()

def test_postgres_concurrent_stock_out():
    # Connect only to medication_inventory_test.
    engine = create_test_engine()

    medication_id = None

    try:
        # Create fictional medication with 10 available units.
        test_medication = MedicationDB(
            name="PostgreSQL Concurrent Stock OUT Test",
            brand="Test Brand",
            ndc="99999999992",
            expiration_date=date(2028, 12, 31),
            lot_number=f"PGCONCURRENT-{uuid.uuid4().hex[:12]}",
            quantity=10,
        )

        with Session(engine) as db:
            db.add(test_medication)
            db.commit()
            db.refresh(test_medication)
            medication_id = test_medication.id

        # Each API request must receive its own database session.
        def override_get_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db

        try:
            # Both workers wait here until they are ready.
            barrier = Barrier(2, timeout=10)

            def perform_stock_out():
                # Synchronize the two requests before sending.
                barrier.wait()

                with TestClient(app) as client:
                    response = client.post(
                        f"/api/medications/{medication_id}/stock-out",
                        json={"quantity": 7},
                    )

                return response.status_code, response.json()

            # Execute both Stock OUT requests concurrently.
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(perform_stock_out)
                    for _ in range(2)
                ]

                results = [
                    future.result(timeout=20)
                    for future in futures
                ]

            status_codes = sorted(
                status_code
                for status_code, _ in results
            )

            # Exactly one request succeeds.
            # The other must be rejected.
            assert status_codes == [201, 409]

            successful_responses = [
                data
                for status_code, data in results
                if status_code == 201
            ]

            assert len(successful_responses) == 1
            assert successful_responses[0]["action"] == "OUT"
            assert successful_responses[0]["quantity"] == 7

            rejected_responses = [
                data
                for status_code, data in results
                if status_code == 409
            ]

            assert len(rejected_responses) == 1
            assert rejected_responses[0]["detail"] == (
                "Insufficient inventory. "
                "Available quantity: 3"
            )

        finally:
            app.dependency_overrides.pop(get_db, None)

        # Verify committed PostgreSQL data.
        with Session(engine) as db:
            saved_medication = db.get(
                MedicationDB,
                medication_id,
            )

            assert saved_medication is not None

            # 10 - 7 = 3.
            assert saved_medication.quantity == 3

            transactions = db.scalars(
                select(InventoryTransactionDB).where(
                    InventoryTransactionDB.medication_id
                    == medication_id
                )
            ).all()

            # Only the successful request should create a record.
            assert len(transactions) == 1
            assert transactions[0].action == "OUT"
            assert transactions[0].quantity == 7

    finally:
        # Remove only records created by this test.
        if medication_id is not None:
            with Session(engine) as db:
                try:
                    transactions = db.scalars(
                        select(InventoryTransactionDB).where(
                            InventoryTransactionDB.medication_id
                            == medication_id
                        )
                    ).all()

                    for transaction in transactions:
                        db.delete(transaction)

                    medication = db.get(
                        MedicationDB,
                        medication_id,
                    )

                    if medication is not None:
                        db.delete(medication)

                    db.commit()

                except Exception:
                    db.rollback()
                    raise

        engine.dispose()
