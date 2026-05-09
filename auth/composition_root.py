from auth.core.app import IAM
from auth.core.token_service import TokenExpeditor
from auth.core.session import SessionManager
from auth.adapters.drivens.jsonUserRepository import JsonUserRepository
from auth.adapters.drivers.passwordAuthenticator import PasswordAuthenticator
from auth.core.domain.user import User
import uuid

def bootstrap_auth():
    user_repo = JsonUserRepository("users.json")
    
    token_expeditor = TokenExpeditor()
    session_manager = SessionManager()
    iam = IAM(user_repo, token_expeditor)
    
    password_auth = PasswordAuthenticator(user_repo)
    
    return iam, password_auth, session_manager

if __name__ == "__main__":
    iam, password_auth, session_manager = bootstrap_auth()
    from auth.adapters.drivers.passwordAuthenticator import PasswordCredential
    
    # Simple test run
    creds = PasswordCredential("admin", "admin")
    token = iam.authenticator(password_auth, creds)
    if token:
        session_manager.set_session(token)
        print(f"Logged in! Token: {session_manager.current_token.encode_token()}")
    else:
        print("Login failed")
