import unittest
from unittest.mock import MagicMock
from tunnelsManager.implants_core import ImplantsUseCase
from tunnelsManager.models.implant import Implant

class TestImplantsUseCase(unittest.TestCase):
    def setUp(self):
        self.repository = MagicMock()
        self.use_case = ImplantsUseCase(self.repository)

    def test_create_implant(self):
        self.repository.save_implant.side_effect = lambda x: x
        implant = self.use_case.create_implant("Test", "python", "payload", "desc")
        
        self.assertEqual(implant.name, "Test")
        self.assertEqual(implant.implant_type, "python")
        self.assertEqual(implant.payload, "payload")
        self.assertIsNotNone(implant.created_at)

    def test_generate_payload_python(self):
        payload = self.use_case.generate_payload(Implant.TYPE_PYTHON, "1.1.1.1", 4444)
        self.assertIn("1.1.1.1", payload)
        self.assertIn("4444", payload)
        self.assertIn("socket", payload)

    def test_generate_payload_powershell(self):
        payload = self.use_case.generate_payload(Implant.TYPE_POWERSHELL, "2.2.2.2", 8888)
        self.assertIn("2.2.2.2", payload)
        self.assertIn("8888", payload)
        self.assertIn("TCPClient", payload)

if __name__ == '__main__':
    unittest.main()
