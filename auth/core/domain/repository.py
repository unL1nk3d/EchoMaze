from dataclasses import dataclass
from typing import Optional

@dataclass
class UserRepository:
    user_id: str
    username: str
    token:str
    is_admin: bool = False
    photo: Optional[str] = None
