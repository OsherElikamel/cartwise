import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class Chain(Base, TimestampMixin):
    """A supermarket chain, identified by its official 13-digit chain code."""

    __tablename__ = "chains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(30), unique=True)
    chain_code: Mapped[str] = mapped_column(String(13), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    name_he: Mapped[str] = mapped_column(String(100))

    stores: Mapped[list["Store"]] = relationship(back_populates="chain", cascade="all, delete-orphan")


class Store(Base, TimestampMixin):
    """One branch. Prices are only ingested for tracked branches."""

    __tablename__ = "stores"
    __table_args__ = (UniqueConstraint("chain_id", "store_code", name="uq_stores_chain_store_code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chains.id"), index=True)
    store_code: Mapped[str] = mapped_column(String(10))
    sub_chain_code: Mapped[str | None] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300))
    city_code: Mapped[str | None] = mapped_column(String(10))
    # The resolved locality: city_code when the chain publishes one, otherwise
    # matched from the branch name (Yohananof publishes city code 0).
    locality_code: Mapped[str | None] = mapped_column(String(10), index=True)
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # Demo branches are what guests compare on; they are never pruned.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    prices_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Last time any user followed this branch; drives pruning of abandoned branches.
    last_followed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    chain: Mapped[Chain] = relationship(back_populates="stores")
