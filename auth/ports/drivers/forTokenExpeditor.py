from abc import ABC, abstractmethod
from auth.core.domain.token import Token
from auth.core.domain.user import User

class ITokenExpeditor(ABC):
    @abstractmethod
    def expedit_token(self, user: User, auth_method: str) -> Token:
        ...

    @abstractmethod
    def ttl_token_policy(self, token: Token) -> bool:
        ...