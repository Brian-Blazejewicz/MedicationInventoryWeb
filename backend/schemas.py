
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: str = Field(min_length=1, max_length=200)
    ndc: str = Field(pattern=r"^[0-9]{11}$")
    expiration_date: date
    lot_number: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=0)


class MedicationResponse(MedicationCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class InventoryTransactionCreate(BaseModel):
    quantity: int = Field(gt=0)


class InventoryTransactionResponse(BaseModel):
    id: int
    medication_id: int
    action: str
    quantity: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

