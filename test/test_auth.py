import unittest
from auth.core.app import IAM
from auth.core.token_service import TokenExpeditor
from auth.adapters.drivers.passwordAuthenticator import PasswordAuthenticator, PasswordCredential
from auth.adapters.drivens.inMemoryUserRepository import InMemoryUserRepository
from auth.core.domain.user import User
from auth.core.domain.token import Token

class TestAuthModule(unittest.TestCase):
    def setUp(self):
        self.user_repo = InMemoryUserRepository()
        self.token_expeditor = TokenExpeditor()
        self.iam = IAM(self.user_repo, self.token_expeditor)
        self.auth_provider = PasswordAuthenticator(self.user_repo)
        
        # Setup a mock user
        self.mock_user = User(user_id="1", username="operator1", roles=["admin"], password="admin")
        self.user_repo.save_user(self.mock_user)

    def test_successful_login(self):
        credentials = PasswordCredential(username="operator1", password="admin")
        token = self.iam.authenticator(self.auth_provider, credentials)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, Token)
        self.assertEqual(token.user, "operator1")
        self.assertEqual(token.encode_token(), "operator1.admin.1.PasswordAuthenticator")

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
        self.assertEqual(saved_user.password, "password123")

    def test_create_user_as_non_admin_fails(self):
        operator_token = Token(user="operator1", roles=["operator"], user_id="1", auth_method="password")
        new_user = User(user_id="3", username="operator3", roles=["operator"])
        
        result = self.iam.create_user(operator_token, new_user)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
