from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    home_locality_code: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
