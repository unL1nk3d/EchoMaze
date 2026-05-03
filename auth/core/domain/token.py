from dataclasses import dataclass

@dataclass
class Token:
    user: str
    roles: list[str]
    user_id: str
    auth_method: str

    def encode_token(self) -> str:
        roles_str = ",".join(self.roles)
        return f"{self.user}.{roles_str}.{self.user_id}.{self.auth_method}"

