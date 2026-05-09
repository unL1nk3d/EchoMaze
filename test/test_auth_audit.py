import unittest
import os
import json
import base64
from auth.adapters.drivens.jsonUserRepository import JsonUserRepository
from auth.adapters.drivers.passwordAuthenticator import PasswordAuthenticator, PasswordCredential
from auth.core.domain.user import User

class TestAuthComponentsAudit(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_users.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.user_repo = JsonUserRepository(self.test_file)
        self.authenticator = PasswordAuthenticator(self.user_repo)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_json_repo_persistence_and_hashing(self):
        # Create a user with a plain text password
        user = User(user_id="1", username="testuser", roles=["op"], password="securepassword")
        self.user_repo.save_user(user)
        
        # Verify it was hashed in memory
        self.assertIsInstance(user.password, dict)
        self.assertIn("salt", user.password)
        self.assertIn("key", user.password)
        
        # Verify persistence
        new_repo = JsonUserRepository(self.test_file)
        loaded_user = new_repo.get_user_by_username("testuser")
        self.assertIsNotNone(loaded_user)
        self.assertEqual(loaded_user.password, user.password)

    def test_password_authenticator_success(self):
        user = User(user_id="1", username="testuser", roles=["op"], password="mypassword")
        self.user_repo.save_user(user)
        
        creds = PasswordCredential(username="testuser", password="mypassword")
        self.assertTrue(self.authenticator.login(creds))

    def test_password_authenticator_wrong_password(self):
        user = User(user_id="1", username="testuser", roles=["op"], password="mypassword")
        self.user_repo.save_user(user)
        
        creds = PasswordCredential(username="testuser", password="wrongpassword")
        self.assertFalse(self.authenticator.login(creds))

    def test_password_authenticator_non_existent_user(self):
        creds = PasswordCredential(username="nobody", password="any")
        self.assertFalse(self.authenticator.login(creds))

    def test_compare_digest_edge_cases(self):
        # Mock user with invalid password format
        user = User(user_id="1", username="baduser", roles=["op"], password="not_a_dict")
        creds = PasswordCredential(username="baduser", password="any")
        self.assertFalse(self.authenticator.compare_digest(user, creds))

if __name__ == "__main__":
    unittest.main()
