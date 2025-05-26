from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    # Add other relevant claims like user_id, roles if needed
    # user_id: Optional[int] = None
    # is_admin: Optional[bool] = None

