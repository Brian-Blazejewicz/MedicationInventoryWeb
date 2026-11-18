from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import SessionLocal

from models import (
    Medication as MedicationDB,
    InventoryTransaction as InventoryTransactionDB,
    User as UserDB,
)

from schemas import (
    MedicationCreate,
    MedicationResponse,
    InventoryTransactionCreate,
    InventoryTransactionResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

from security import hash_password, verify_password
from auth import create_access_token, verify_access_token
from jwt.exceptions import InvalidTokenError



app = FastAPI(
    title="Medication Inventory API",
    description="REST API for the Medication Inventory application",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class Medication(BaseModel):
    id: int
    name: str
    brand: str
    ndc: str


# Fabricated sample records for development and testing.
sample_medications = [
    Medication(
        id=1,
        name="Acetaminophen 500 mg",
        brand="Sample Brand A",
        ndc="00000000001",
    ),
    Medication(
        id=2,
        name="Ibuprofen 200 mg",
        brand="Sample Brand B",
        ndc="00000000002",
    ),
    Medication(
        id=3,
        name="Loratadine 10 mg",
        brand="Sample Brand C",
        ndc="00000000003",
    ),
]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Require a Bearer token for protected endpoints.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> UserDB:
    """Validate a JWT and retrieve the authenticated user."""

    authentication_error = HTTPException(
        status_code=401,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise authentication_error

    try:
        user_id = verify_access_token(credentials.credentials)
    except (InvalidTokenError, ValueError):
        raise authentication_error

    user = db.get(UserDB, user_id)

    if user is None or not user.is_active:
        raise authentication_error

    return user


@app.post(
    "/api/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    # Normalize the email address.
    email = user_data.email.strip().lower()

    # Check whether the email is already registered.
    existing_user = db.scalar(
        select(UserDB).where(UserDB.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    # Hash the password before storing it.
    new_user = UserDB(
        email=email,
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    return new_user

@app.post("/api/auth/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    email = user_data.email.strip().lower()

    user = db.scalar(
        select(UserDB).where(UserDB.email == email)
    )

    if user is None or not verify_password(
        user_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="This account is inactive.",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/api/auth/me", response_model=UserResponse)
def get_my_profile(
    current_user: UserDB = Depends(get_current_user),
):
    """Return the currently authenticated user's profile."""
    return current_user


@app.get("/")
def home():
    return {
        "message": "Welcome to the Medication Inventory API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Medication Inventory API",
    }


@app.get(
    "/api/medications",
    response_model=list[MedicationResponse],
)
def get_medications(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    medications = (
        db.query(MedicationDB)
        .order_by(MedicationDB.id)
        .all()
    )

    return medications


@app.post(
    "/api/medications",
    response_model=MedicationResponse,
    status_code=201,
)

def create_medication(
    medication: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    new_medication = MedicationDB(
        **medication.model_dump()
    )

    db.add(new_medication)

    try:
        db.commit()
        db.refresh(new_medication)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Medication with this NDC and lot number already exists, or a database constraint was violated.",
        )

    return new_medication


@app.get(
    "/api/medications/{medication_id}",
    response_model=MedicationResponse,
)

def get_medication_by_id(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    medication = db.get(MedicationDB, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=404,
            detail="Medication not found",
        )

    return medication


@app.put(
    "/api/medications/{medication_id}",
    response_model=MedicationResponse,
)
def update_medication(
    medication_id: int,
    updated_data: MedicationCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    medication = db.get(MedicationDB, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=404,
            detail="Medication not found",
        )

    for field, value in updated_data.model_dump().items():
        setattr(medication, field, value)

    try:
        db.commit()
        db.refresh(medication)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Medication update violates a database constraint",
        )

    return medication

@app.delete(
    "/api/medications/{medication_id}",
    status_code=204,
)
def delete_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    medication = db.get(MedicationDB, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=404,
            detail="Medication not found",
        )

    db.delete(medication)
    db.commit()

    return None


@app.get(
    "/api/medications/{medication_id}/transactions",
    response_model=list[InventoryTransactionResponse],
)

def get_medication_transactions(
    medication_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    # Confirm that the medication exists.
    medication = db.get(MedicationDB, medication_id)

    if medication is None:
        raise HTTPException(
            status_code=404,
            detail="Medication not found",
        )

    # Retrieve the medication's transaction history.
    transactions = (
        db.query(InventoryTransactionDB)
        .filter(
            InventoryTransactionDB.medication_id == medication_id
        )
        .order_by(
            InventoryTransactionDB.timestamp.desc(),
            InventoryTransactionDB.id.desc(),
        )
        .all()
    )

    return transactions


@app.post(
    "/api/medications/{medication_id}/stock-in",
    response_model=InventoryTransactionResponse,
    status_code=201,
)

def stock_in(
    medication_id: int,
    transaction_data: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    try:
        # Lock the medication row until the transaction finishes.
        medication = db.execute(
            select(MedicationDB)
            .where(MedicationDB.id == medication_id)
            .with_for_update()
        ).scalar_one_or_none()

        if medication is None:
            raise HTTPException(
                status_code=404,
                detail="Medication not found",
            )

        # Increase the current inventory quantity.
        medication.quantity += transaction_data.quantity

        # Record the stock movement.
        transaction = InventoryTransactionDB(
            medication_id=medication.id,
            action="IN",
            quantity=transaction_data.quantity,
        )

        db.add(transaction)

        # Commit the quantity change and history together.
        db.commit()

        # Load generated transaction ID and timestamp.
        db.refresh(transaction)

        return transaction

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


@app.post(
    "/api/medications/{medication_id}/stock-out",
    response_model=InventoryTransactionResponse,
    status_code=201,
)

def stock_out(
    medication_id: int,
    transaction_data: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):

    try:
        # Lock the medication row to prevent concurrent
        # stock operations from corrupting the quantity.
        medication = db.execute(
            select(MedicationDB)
            .where(MedicationDB.id == medication_id)
            .with_for_update()
        ).scalar_one_or_none()

        if medication is None:
            raise HTTPException(
                status_code=404,
                detail="Medication not found",
            )

        # Reject requests that exceed available inventory.
        if transaction_data.quantity > medication.quantity:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Insufficient inventory. "
                    f"Available quantity: {medication.quantity}"
                ),
            )

        # Decrease the medication quantity.
        medication.quantity -= transaction_data.quantity

        # Create the corresponding inventory transaction.
        transaction = InventoryTransactionDB(
            medication_id=medication.id,
            action="OUT",
            quantity=transaction_data.quantity,
        )

        db.add(transaction)

        # Save both changes atomically.
        db.commit()

        # Load the generated transaction ID and timestamp.
        db.refresh(transaction)

        return transaction

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
