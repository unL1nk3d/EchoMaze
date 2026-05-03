from typing import Optional
from auth.core.domain.auth import IAuthenticatorProvider, ICredential
from auth.ports.drivers.forAuthentication import Authenticate
from auth.ports.drivers.forTokenExpeditor import ITokenExpeditor
from auth.core.domain.token import Token
from auth.core.domain.user import User
from auth.ports.drivens.forRepository import IUserRepository

class IAM(Authenticate):
    def __init__(self, user_repo: IUserRepository, token_expeditor: ITokenExpeditor):
        self.user_repo = user_repo
        self.token_expeditor = token_expeditor

    def authenticator(self, auth_provider: IAuthenticatorProvider, credentials: ICredential) -> Optional[Token]:
        if auth_provider.login(credentials):
            username = getattr(credentials, 'username', None)
            if username:
                user = self.user_repo.get_user_by_username(username)
                if user:
                    return self.token_expeditor.expedit_token(user, auth_provider.__class__.__name__)
        return None

    def create_user(self, admin_token: Token, new_user: User) -> bool:
        # Check if the person performing the action is an admin
        if "admin" not in admin_token.roles:
            print("[!] Access denied: Only administrators can create users.")
            return False
        
        existing = self.user_repo.get_user_by_username(new_user.username)
        if existing:
            print(f"[!] User {new_user.username} already exists.")
            return False
            
        self.user_repo.save_user(new_user)
        return True
