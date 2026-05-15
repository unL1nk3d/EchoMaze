import subprocess
from typing import List, Dict, Any
from agenticLLM.models.agent import Skill
from agenticLLM.ports.drivens.forSkills import ForSkillRegistry

class CLISkillExecutorAdapter(ForSkillRegistry):
    """
    Adapter to manage and execute modular 'Skills' via CLI or internal calls.
    """
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._callbacks: Dict[str, callable] = {}
        self._load_default_skills()

    def register_skill(self, skill: Skill, callback: callable):
        self._skills[skill.name] = skill
        self._callbacks[skill.name] = callback

    def list_available_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def execute_skill(self, name: str, params: Dict[str, Any]) -> str:
        if name not in self._callbacks:
            return f"Error: Skill '{name}' not found."
        
        try:
            return str(self._callbacks[name](**params))
        except Exception as e:
            return f"Error executing skill '{name}': {str(e)}"

    def _load_default_skills(self):
        # Skill: Ping Discovery
        self.register_skill(
            Skill(
                name="run_ping",
                description="Checks connectivity to a host using ping.",
                usage_example="run_ping(host='127.0.0.1')",
                category="discovery"
            ),
            self._ping_callback
        )
        
        # Skill: Custom Shell Command (use with caution!)
        self.register_skill(
            Skill(
                name="run_shell",
                description="Executes an arbitrary shell command (Read-only intended).",
                usage_example="run_shell(cmd='whoami')",
                category="utility",
                requires_approval=True
            ),
            self._shell_callback
        )

    def _ping_callback(self, host: str):
        # Simple cross-platform ping simulation
        import os
        param = '-n' if os.name == 'nt' else '-c'
        command = ['ping', param, '1', host]
        res = subprocess.run(command, capture_output=True, text=True)
        return res.stdout if res.returncode == 0 else f"Host {host} is unreachable."

    def _shell_callback(self, cmd: str):
        # DANGER: In a real app, this should be highly restricted
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return res.stdout or res.stderr
        except Exception as e:
            return str(e)
