from auth.ports.drivers.forTokenExpeditor import ITokenExpeditor
from auth.core.domain.token import Token
from auth.core.domain.user import User

class TokenExpeditor(ITokenExpeditor):
    def expedit_token(self, user: User, auth_method: str, restricted: bool = False) -> Token:
        return Token(
            user=user.username,
            roles=user.roles,
            user_id=user.user_id,
            auth_method=auth_method,
            restricted=restricted
        )

    def ttl_token_policy(self, token: Token) -> bool:
        # Simple policy for now
        return True
