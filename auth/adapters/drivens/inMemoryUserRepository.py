from typing import Optional, Dict
from auth.ports.drivens.forRepository import IUserRepository
from auth.core.domain.user import User

class InMemoryUserRepository(IUserRepository):
    def __init__(self):
        self._users: Dict[str, User] = {"blake":User(1,'blake',['operator','admin'],True)}

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def save_user(self, user: User):
        self._users[user.username] = user
