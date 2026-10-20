import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base, TimestampMixin


class ItemMatch(Base, TimestampMixin):
    """A user's remembered answer to "which product do I mean by this, at this chain".

    Keyed by chain, not branch: a barcode is the same product at every branch
    of a chain, so a choice made at one branch carries over to the others.
    """

    __tablename__ = "item_matches"
    __table_args__ = (UniqueConstraint("user_id", "chain_id", "match_key", name="uq_item_matches_user_chain_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chains.id", ondelete="CASCADE"))
    match_key: Mapped[str] = mapped_column(String(200))
    item_code: Mapped[str] = mapped_column(String(20))
    item_name: Mapped[str] = mapped_column(String(300))
