from abc import ABC, abstractmethod
from auth.core.domain.auth import IAuthenticatorProvider, ICredential

class CreateUser(ABC):
    @abstractmethod
    def create(self, auth_provider: IAuthenticatorProvider, credentials: ICredential,userDetails:User):
        ...