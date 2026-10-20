from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class Locality(Base):
    """A city, town or village from the official list, keyed by its government code
    (the same code the chains publish in their Stores files)."""

    __tablename__ = "localities"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name_he: Mapped[str] = mapped_column(String(100), index=True)
    name_en: Mapped[str] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
