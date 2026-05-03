from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: str
    username: str
    roles: list[str]
    is_admin: bool = False
    photo: Optional[str] = None
    password: Optional[str] = None

    def validate_token(self, token: bytes):
        if not isinstance(token, bytes):
            raise ValueError('the data need to be a bytes object!')
        return True