
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    brand: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    ndc: Mapped[str] = mapped_column(
        String(11), nullable=False
    )

    expiration_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    lot_number: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    __table_args__ = (
        UniqueConstraint(
            "ndc",
            "lot_number",
            name="uq_medication_ndc_lot",
        ),
        CheckConstraint(
            "quantity >= 0",
            name="ck_medication_quantity_nonnegative",
        ),
        CheckConstraint(
            "ndc ~ '^[0-9]{11}$'",
            name="ck_medication_ndc_format",
        ),
    )

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    medication_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medications.id", ondelete="RESTRICT"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('IN', 'OUT')",
            name="ck_inventory_transaction_action",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_inventory_transaction_quantity_positive",
        ),
    )
