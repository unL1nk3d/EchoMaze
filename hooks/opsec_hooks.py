"""
hooks/opsec_hooks.py
Hooks for integrating OpSec/tactical suggestions into UI/core events.
"""

from core.tactical_suggestions import TacticalSuggestions

class OpSecHooks:
    """
    Connects tactical suggestions to UI or core logic.
    Designed for easy extension/integration.
    """
    def __init__(self, ts=None):
        self.ts = ts or TacticalSuggestions()

    def on_noise_score_update(self, noise_score: int) -> str:
        """
        Reacts to an updated noise score and returns related OpSec advice.
        """
        return self.ts.get_noise_advice(noise_score)

    def on_service_selected(self, service: str) -> list:
        """
        Returns OpSec suggestions when a user inspects a service.
        """
        return self.ts.suggest_for_service(service)

    def on_pivot_path_change(self, path: list) -> list:
        """
        Returns tactical OpSec suggestions for the current pivot path.
        """
        return self.ts.pivot_path_advice(path)
