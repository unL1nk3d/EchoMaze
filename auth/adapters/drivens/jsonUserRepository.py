import json
import os
import hashlib
import base64
import hmac
from typing import Optional, Dict
from auth.ports.drivens.forRepository import IUserRepository
from auth.core.domain.user import User

class JsonUserRepository(IUserRepository):
    BOOTSTRAP_SALT = b"EchoMazeDefaultAdminSalt"
    
    def __init__(self, file_path: str = "users.json"):
        self.file_path = file_path
        self._users: Dict[str, User] = {}
        # Derive the system signing key from the default admin credentials (admin:admin)
        self._signing_key = hashlib.pbkdf2_hmac(
            'sha256', 
            b"admin", 
            self.BOOTSTRAP_SALT, 
            100_000, 
            dklen=32
        )
        self._load()

    def _hash_new_password(self, password: str, key_len: int = 32) -> dict:
        salt = os.urandom(16)
        iterations = 100_000
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=key_len)
        return {
            "salt": base64.b64encode(salt).decode(),
            "iterations": iterations,
            "key": base64.b64encode(key).decode()
        }

    def _sign_token(self, data: dict) -> str:
        payload = base64.b64encode(json.dumps(data).encode()).decode()
        signature = hmac.new(self._signing_key, payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}.{signature}"

    def _verify_token(self, token: str) -> Optional[dict]:
        try:
            payload_b64, signature = token.split('.')
            expected_signature = hmac.new(self._signing_key, payload_b64.encode(), hashlib.sha256).hexdigest()
            if hmac.compare_digest(signature, expected_signature):
                return json.loads(base64.b64decode(payload_b64).decode())
        except Exception:
            pass
        return None

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        token = user_data.get('token')
                        if token:
                            payload = self._verify_token(token)
                            if payload:
                                user = User(
                                    user_id=payload['user_id'],
                                    username=username,
                                    roles=payload['roles'],
                                    is_admin=payload['is_admin'],
                                    photo=payload.get('photo'),
                                    password=user_data.get('password'),
                                    requires_password_change=payload.get('requires_password_change', False)
                                )
                                self._users[username] = user
                            else:
                                print(f"[!] Invalid token for user {username}")
            except Exception as e:
                print(f"[!] Error loading users: {e}")

    def _save(self):
        data = {}
        for username, user in self._users.items():
            password_data = user.password
            if isinstance(password_data, str):
                password_data = self._hash_new_password(password_data)
                user.password = password_data

            token_payload = {
                "user_id": user.user_id,
                "roles": user.roles,
                "is_admin": user.is_admin,
                "photo": user.photo,
                "requires_password_change": user.requires_password_change
            }
            
            data[username] = {
                "token": self._sign_token(token_payload),
                "password": password_data
            }
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def save_user(self, user: User):
        self._users[user.username] = user
        self._save()
