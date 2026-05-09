from abc import ABC, abstractmethod

class ICredential(ABC):
    @abstractmethod
    def validate(self) -> bool:
        ...

class IAuthenticatorProvider(ABC):
    @abstractmethod
    def login(self, credentials: ICredential) -> bool:
        ...
