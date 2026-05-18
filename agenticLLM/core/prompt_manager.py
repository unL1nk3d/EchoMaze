import json
import os
from typing import Dict, Any, Optional

class PromptManager:
    """Manages system prompts and templates dynamically."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._prompts = {}
            cls._instance._load_default_prompts()
        return cls._instance
    
    def _load_default_prompts(self):
        # Determine the path to the JSON file
        base_dir = os.path.dirname(os.path.dirname(__file__))
        json_path = os.path.join(base_dir, "prompts", "system_prompts.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    self._prompts = data.get("system_prompts", {})
            except Exception as e:
                print(f"Error loading system prompts from JSON: {e}")
                self._prompts = {}
        else:
             print(f"Warning: Prompt file not found at {json_path}")
             self._prompts = {}

    def get_prompt(self, key: str, default: Optional[str] = None) -> str:
        """Retrieves a prompt by key."""
        return self._prompts.get(key, default or "")

    def set_prompt(self, key: str, value: str):
        """Dynamically updates or adds a prompt."""
        self._prompts[key] = value

    def list_keys(self):
        """Lists all available prompt keys."""
        return list(self._prompts.keys())

    def reload(self):
        """Reloads prompts from the JSON file."""
        self._load_default_prompts()
