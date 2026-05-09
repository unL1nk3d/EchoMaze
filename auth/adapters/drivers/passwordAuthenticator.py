from auth.core.domain.auth import IAuthenticatorProvider, ICredential
from dataclasses import dataclass
import hashlib
import base64
import hmac

@dataclass
class PasswordCredential(ICredential):
    username: str
    password: str

    def validate(self) -> bool:
        return len(self.username) > 0 and len(self.password) > 0

    def hash_password(self, salt: bytes, iterations: int, key_len: int = 32) -> bytes:
        return hashlib.pbkdf2_hmac(
            'sha256', 
            self.password.encode('utf-8'), 
            salt, 
            iterations, 
            dklen=key_len
        )

class PasswordAuthenticator(IAuthenticatorProvider):
    def __init__(self, user_repo):
        self.user_repo = user_repo

    def compare_digest(self, user, credentials: PasswordCredential) -> bool:
        try:
            stored_value = user.password
            if not isinstance(stored_value, dict):
                return False
            
            salt = base64.b64decode(stored_value['salt'])
            iterations = int(stored_value['iterations'])
            stored_key = base64.b64decode(stored_value['key'])
            
            computed_key = credentials.hash_password(salt, iterations)
            return hmac.compare_digest(stored_key, computed_key)
        except Exception:
            return False

    def login(self, credentials: PasswordCredential) -> bool:
        if not isinstance(credentials, PasswordCredential):
            return False

        user = self.user_repo.get_user_by_username(credentials.username)
        if user and self.compare_digest(user, credentials):
            return True
        return False
