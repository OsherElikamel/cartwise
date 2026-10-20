from app.db.base_class import Base  # noqa: F401

# Import all models so Alembic can see them
from app.models.user import User  # noqa: F401
from app.models.chain import Chain, Store  # noqa: F401
from app.models.store_item import StoreItem  # noqa: F401
from app.models.promotion import Promotion  # noqa: F401
