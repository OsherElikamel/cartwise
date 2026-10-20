import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin, utcnow


class ShoppingList(Base, TimestampMixin):
    """A list the user runs again and again, e.g. the weekly shop.

    parsed_items caches the AI's reading of `text`; it is cleared whenever the
    text changes, so an unchanged list never needs the parsing call again.
    """

    __tablename__ = "shopping_lists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(Text)
    parsed_items: Mapped[list | None] = mapped_column(JSONB)


class BasketRun(Base):
    """One comparison a signed-in user ran: a summary for the history page and
    the full result to reopen it, frozen at the prices of that day."""

    __tablename__ = "basket_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    list_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("shopping_lists.id", ondelete="SET NULL"))
    item_count: Mapped[int]
    cheapest_chain: Mapped[str] = mapped_column(String(100))
    cheapest_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    savings: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    result: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
