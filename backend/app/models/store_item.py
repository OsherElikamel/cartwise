import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, utcnow


class StoreItem(Base):
    """A product as one branch sells it, with that branch's current price.

    item_code is the barcode for packaged goods (item_type 1), so the same
    product can be compared across chains. Produce and deli items use
    chain-internal codes (item_type 0) and are matched by name instead.
    """

    __tablename__ = "store_items"
    __table_args__ = (
        Index("ix_store_items_item_code", "item_code"),
        Index(
            "ix_store_items_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True)
    item_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    item_type: Mapped[int] = mapped_column(default=1)
    name: Mapped[str] = mapped_column(String(300))
    manufacturer: Mapped[str | None] = mapped_column(String(200))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    unit: Mapped[str | None] = mapped_column(String(50))
    is_weighted: Mapped[bool] = mapped_column(Boolean, default=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    price_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
