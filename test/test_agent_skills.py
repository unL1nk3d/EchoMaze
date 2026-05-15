import unittest
from unittest.mock import MagicMock
from agenticLLM.adapters.drivens.SkillExecutorAdapter import CLISkillExecutorAdapter
from agenticLLM.models.agent import Skill

class TestAgentSkills(unittest.TestCase):
    def setUp(self):
        self.registry = CLISkillExecutorAdapter()

    def test_default_skills_loaded(self):
        skills = self.registry.list_available_skills()
        names = [s.name for s in skills]
        self.assertIn("run_ping", names)
        self.assertIn("run_shell", names)

    def test_execute_ping_skill(self):
        # We can't easily run a real ping in CI reliably, so we mock the callback if needed
        # but let's test the registry delegation
        result = self.registry.execute_skill("run_ping", {"host": "127.0.0.1"})
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_custom_skill_registration(self):
        def my_custom_tool(target):
            return f"Hacking {target}..."
        
        self.registry.register_skill(
            Skill(name="exploit_x", description="Custom exploit", usage_example="exploit_x(target='...')"),
            my_custom_tool
        )
        
        result = self.registry.execute_skill("exploit_x", {"target": "10.0.0.1"})
        self.assertEqual(result, "Hacking 10.0.0.1...")

    def test_execute_non_existent_skill(self):
        result = self.registry.execute_skill("ghost_skill", {})
        self.assertIn("not found", result)

if __name__ == '__main__':
    unittest.main()
