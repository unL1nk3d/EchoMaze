from dataclasses import dataclass

@dataclass
class Token:
    user: str
    roles: list[str]
    user_id: str
    auth_method: str
    restricted: bool = False

    def encode_token(self) -> str:
        roles_str = ",".join(self.roles)
        restriction = "restricted" if self.restricted else "unrestricted"
        return f"{self.user}.{roles_str}.{self.user_id}.{self.auth_method}.{restriction}"

