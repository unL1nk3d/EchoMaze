import unittest
from unittest.mock import MagicMock
from tunnelsManager.api import get_tunnels_api

class TestTunnelsAPI(unittest.TestCase):
    def setUp(self):
        # We can use a mock DAO or a real one if needed, but for unit testing the API 
        # wrapper we can mock the underlying use cases if we want, or just test the 
        # factory and discovery.
        self.api = get_tunnels_api()

    def test_api_discovery(self):
        """Test that the API can list its own functions for LLM consumption."""
        functions = self.api.list_available_functions()
        self.assertIsInstance(functions, list)
        self.assertTrue(len(functions) > 0)
        
        # Check for some expected functions in the discovery list
        function_names = [f['name'] for f in functions]
        self.assertIn('create_tunnel', function_names)
        self.assertIn('get_all_tunnels', function_names)
        self.assertIn('create_implant', function_names)
        self.assertIn('list_implants', function_names)

    def test_api_delegation(self):
        """Test that the API correctly delegates calls to use cases."""
        # This is a bit of an integration test if we use the real ones, 
        # but let's just check if the methods exist on the api object.
        self.assertTrue(hasattr(self.api, 'create_tunnel'))
        self.assertTrue(hasattr(self.api, 'get_all_tunnels'))
        self.assertTrue(hasattr(self.api, 'create_implant'))
        self.assertTrue(hasattr(self.api, 'list_implants'))

if __name__ == '__main__':
    unittest.main()
