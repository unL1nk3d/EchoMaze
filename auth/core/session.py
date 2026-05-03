from typing import Optional
from auth.core.domain.token import Token

class SessionManager:
    def __init__(self):
        self._current_token: Optional[Token] = None

    def set_session(self, token: Token):
        self._current_token = token

    def clear_session(self):
        self._current_token = None

    @property
    def current_token(self) -> Optional[Token]:
        return self._current_token

    def is_authenticated(self) -> bool:
        return self._current_token is not None
