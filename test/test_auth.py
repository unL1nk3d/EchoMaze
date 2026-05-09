import unittest
import os
from auth.core.app import IAM
from auth.core.token_service import TokenExpeditor
from auth.adapters.drivers.passwordAuthenticator import PasswordAuthenticator, PasswordCredential
from auth.core.domain.user import User
from auth.core.domain.token import Token
from auth.adapters.drivens.jsonUserRepository import JsonUserRepository

class TestAuthModule(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_auth_module.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.user_repo = JsonUserRepository(self.test_file)
        self.token_expeditor = TokenExpeditor()
        self.iam = IAM(self.user_repo, self.token_expeditor)
        self.auth_provider = PasswordAuthenticator(self.user_repo)

        # Setup a mock user
        self.mock_user = User(user_id="1", username="operator1", roles=["admin"], password="admin")
        self.user_repo.save_user(self.mock_user)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_successful_login(self):
        credentials = PasswordCredential(username="operator1", password="admin")
        token = self.iam.authenticator(self.auth_provider, credentials)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, Token)
        self.assertEqual(token.user, "operator1")
        # Note: auth_method is now the class name in IAM
        self.assertEqual(token.encode_token(), "operator1.admin.1.PasswordAuthenticator.unrestricted")

    def test_failed_login_wrong_password(self):
        credentials = PasswordCredential(username="operator1", password="wrong")
        token = self.iam.authenticator(self.auth_provider, credentials)
        self.assertIsNone(token)

    def test_create_user_as_admin(self):
        admin_token = Token(user="admin", roles=["admin"], user_id="0", auth_method="password")
        new_user = User(user_id="2", username="operator2", roles=["operator"], password="password123")
        
        result = self.iam.create_user(admin_token, new_user)
        self.assertTrue(result)
        
        # Verify user was saved
        saved_user = self.user_repo.get_user_by_username("operator2")
        self.assertIsNotNone(saved_user)
        # It will be a dict now, but we check if login works
        creds = PasswordCredential(username="operator2", password="password123")
        self.assertTrue(self.auth_provider.login(creds))

    def test_create_user_as_non_admin_fails(self):
        operator_token = Token(user="operator1", roles=["operator"], user_id="1", auth_method="password")
        new_user = User(user_id="3", username="operator3", roles=["operator"])
        
        result = self.iam.create_user(operator_token, new_user)
        self.assertFalse(result)

    def test_forced_password_reset_flow(self):
        # 1. Admin creates a user (it will have requires_password_change=True by default in handle_register, 
        # but here we test the IAM/Domain logic)
        new_user = User(
            user_id="4", 
            username="temp_user", 
            roles=["operator"], 
            password="temp_password", 
            requires_password_change=True
        )
        self.user_repo.save_user(new_user)
        
        # 2. Login with temp user
        creds = PasswordCredential(username="temp_user", password="temp_password")
        token = self.iam.authenticator(self.auth_provider, creds)
        
        # 3. Verify token is restricted
        self.assertIsNotNone(token)
        self.assertTrue(token.restricted)
        self.assertIn("restricted", token.encode_token())
        
        # 4. Change password
        result = self.iam.change_password(token, "new_secure_password")
        self.assertTrue(result)
        
        # 5. Verify user is no longer restricted
        updated_user = self.user_repo.get_user_by_username("temp_user")
        self.assertFalse(updated_user.requires_password_change)
        
        # 6. Login again and verify token is unrestricted
        new_creds = PasswordCredential(username="temp_user", password="new_secure_password")
        new_token = self.iam.authenticator(self.auth_provider, new_creds)
        self.assertIsNotNone(new_token)
        self.assertFalse(new_token.restricted)
        self.assertIn("unrestricted", new_token.encode_token())

if __name__ == "__main__":
    unittest.main()
