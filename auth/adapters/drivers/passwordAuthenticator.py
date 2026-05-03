from auth.core.domain.auth import IAuthenticatorProvider, ICredential
from dataclasses import dataclass

@dataclass
class PasswordCredential(ICredential):
    username: str
    password: str

    def validate(self) -> bool:
        return len(self.username) > 0 and len(self.password) > 0

class PasswordAuthenticator(IAuthenticatorProvider):
    def __init__(self, user_repo):
        self.user_repo = user_repo

    def login(self, credentials: PasswordCredential) -> bool:
        if not isinstance(credentials, PasswordCredential):
            return False

        user = self.user_repo.get_user_by_username(credentials.username)
        if user and user.password == credentials.password:
            return True
        return False

