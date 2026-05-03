from abc import ABC, abstractmethod
from auth.core.domain.auth import IAuthenticatorProvider, ICredential

class Authenticate(ABC):
    @abstractmethod
    def authenticator(self, auth_provider: IAuthenticatorProvider, credentials: ICredential) -> bool:
        ...