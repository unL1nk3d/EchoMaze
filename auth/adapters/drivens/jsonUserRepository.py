import json
import os
import hashlib
import base64
from typing import Optional, Dict
from auth.ports.drivens.forRepository import IUserRepository
from auth.core.domain.user import User

class JsonUserRepository(IUserRepository):
    def __init__(self, file_path: str = "users.json"):
        self.file_path = file_path
        self._users: Dict[str, User] = {}
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

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        user = User(
                            user_id=user_data['user_id'],
                            username=user_data['username'],
                            roles=user_data['roles'],
                            is_admin=user_data.get('is_admin', False),
                            photo=user_data.get('photo')
                        )
                        # password here is the dict with salt, iterations, key
                        user.password = user_data.get('password')
                        self._users[username] = user
            except Exception as e:
                print(f"[!] Error loading users: {e}")

    def _save(self):
        data = {}
        for username, user in self._users.items():
            # If user.password is a string (newly set), hash it.
            # If it's already a dict, it's already hashed.
            password_data = user.password
            if isinstance(password_data, str):
                password_data = self._hash_new_password(password_data)
                user.password = password_data # Update in-memory too

            data[username] = {
                'user_id': user.user_id,
                'username': user.username,
                'roles': user.roles,
                'is_admin': user.is_admin,
                'photo': user.photo,
                'password': password_data
            }
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def save_user(self, user: User):
        self._users[user.username] = user
        self._save()
