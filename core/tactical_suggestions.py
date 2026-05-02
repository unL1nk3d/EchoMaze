"""
core/tactical_suggestions.py
Tactical suggestion and OpSec advice provider for EchoMaze operations.
"""

from typing import List, Dict
from UI.models import Observable

class TacticalSuggestions(Observable):
    """
    Provides OpSec-related tactical suggestions based on context (noise score, techniques, services).
    Follows Clean/DAO architecture conventions.
    Extends Observable to emit tactics_changed events.
    """
    
    def __init__(self):
        super().__init__()

    def get_noise_advice(self, score: int) -> str:
        """
        Returns OpSec advice based on a noise score.
        Args:
            score (int): The noise score (0-100+)
        Returns:
            str: Tactical suggestion for OpSec.
        """
        if score < 25:
            advice = "Stealth optimal. Continue controlled, quiet operation."
        elif score < 50:
            advice = "Notable activity detected. Minimize scans and brute force actions. Consider cleanup."
        elif score < 75:
            advice = "High noise! Immediate stealth measures required. Reduce traffic and rotate techniques."
        else:
            advice = "Critical exposure. Stop and review your attack surface. Consider fallback and evasion."
        self.notify("tactics_changed", {"advice": advice, "score": score})
        return advice

    def suggest_for_service(self, service: str) -> List[str]:
        """
        Suggests OpSec-sensitive tactics for a given network service.
        Args:
            service (str): e.g. 'smb', 'http', 'rdp'
        Returns:
            list[str]: Suggestions appropriate for the service
        """
        service_lower = service.lower()
        suggestions_map = {
            'smb': ["Avoid noisy null sessions.", "Watch for account lockouts.", "Use stealthy shares enumeration."],
            'rdp': ["Limit connection attempts.", "Leverage valid credentials only.", "Monitor for blue team activity."],
            'http': ["Throttle brute-force logins.", "Blend user-agent strings.", "Check for WAF presence."],
            'dns': ["Prefer passive or subdomain enumeration.", "Avoid zone transfers unless safe.", "Consider DNS tunneling only as a last resort."]
        }
        suggestions = suggestions_map.get(service_lower, ["Standard OpSec, minimize detection techniques."])
        self.notify("tactics_changed", {"suggestions": suggestions, "service": service})
        return suggestions

    def pivot_path_advice(self, path: List[str]) -> List[str]:
        """
        Provides recommendations based on a pivoting path (list of IPs or nodes traversed).
        Args:
            path (List[str]): The path of nodes/IPs.
        Returns:
            List[str]: List of suggestions for the current pivoting state.
        """
        if len(path) < 2:
            adv = ["Minimal lateral movement—risk low."]
        else:
            adv = ["Each pivot increases detection odds. Delete residual artifacts.",
                   "Rotate tools/methods at each step.",
                   f"Current pivot chain length: {len(path)}"]
            if len(path) > 4:
                adv.append("Warning: Deep pivoting. Assume blue team monitoring is likely.")
        self.notify("tactics_changed", {"suggestions": adv, "path": path})
        return adv
