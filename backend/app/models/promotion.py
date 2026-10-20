import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, utcnow


class Promotion(Base):
    """A price promotion on one item at one branch.

    Only promotions open to all shoppers (club 0) are stored. A promotion
    with several items becomes one row per item. effective_unit_price is
    computed at ingest: discounted_price covers min_qty units ("3 for 10"),
    or one kilo for weighted items.
    """

    __tablename__ = "promotions"

    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True)
    promotion_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    item_code: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(300))
    min_qty: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    discounted_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    effective_unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
