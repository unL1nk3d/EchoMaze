import json
import os
from typing import Optional, Dict
from auth.ports.drivens.forRepository import IUserRepository
from auth.core.domain.user import User

class JsonUserRepository(IUserRepository):
    def __init__(self, file_path: str = "users.json"):
        self.file_path = file_path
        self._users: Dict[str, User] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        # Extract password if present, but User domain might not have it
                        # We'll store it in the JSON but maybe not in the domain User object
                        # if we want to follow strict hexagonal.
                        # For simplicity, let's just store everything.
                        self._users[username] = User(
                            user_id=user_data['user_id'],
                            username=user_data['username'],
                            roles=user_data['roles'],
                            is_admin=user_data.get('is_admin', False),
                            photo=user_data.get('photo')
                        )
                        # We might need to store the password somewhere else or in the User object
                        # Let's add password to the domain for now to keep it practical
                        self._users[username].password = user_data.get('password')
            except Exception as e:
                print(f"[!] Error loading users: {e}")

    def _save(self):
        data = {}
        for username, user in self._users.items():
            data[username] = {
                'user_id': user.user_id,
                'username': user.username,
                'roles': user.roles,
                'is_admin': user.is_admin,
                'photo': user.photo,
                'password': getattr(user, 'password', None)
            }
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def save_user(self, user: User):
        self._users[user.username] = user
        self._save()
