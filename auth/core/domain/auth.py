from abc import ABC, abstractmethod

class ICredential(ABC):
    @abstractmethod
    def validate(self) -> bool:
        ...

class CredentialSerialized(ABC):
    @abstractmethod
    def get_credentials(self, credential: ICredential):
        ...

class IAuthenticatorProvider(ABC):
    @abstractmethod
    def login(self, credentials: ICredential) -> bool:
        ...


