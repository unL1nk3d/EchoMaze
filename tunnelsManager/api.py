from typing import List, Dict, Any
import inspect
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.implants_core import ImplantsUseCase
from tunnelsManager.adapters.drivens.RepositoryImpl import DatabaseTunnelRepository, DatabaseImplantRepository
from tunnelsManager.adapters.drivens.ConnectionTestImpl import NetworkConnectionTester
from GATHERINGDB.main import GenericDAO

class TunnelsManagerAPI:
    """
    Unified API for Tunnels and Implants management.
    This class exposes all functionalities from TunnelsUseCase and ImplantsUseCase
    to be easily consumed by an LLM or other external components.
    """
    def __init__(self, tunnels_usecase: TunnelsUseCase, implants_usecase: ImplantsUseCase):
        self.tunnels = tunnels_usecase
        self.implants = implants_usecase
        
        # Proxy methods from TunnelsUseCase
        self.create_tunnel = self.tunnels.create_tunnel
        self.advance_tunnel_phase = self.tunnels.advance_tunnel_phase
        self.setup_tunnel = self.tunnels.setup_tunnel
        self.register_interface = self.tunnels.register_interface
        self.set_ready = self.tunnels.set_ready
        self.get_all_tunnels = self.tunnels.get_all_tunnels
        self.get_hanging_tunnels = self.tunnels.get_hanging_tunnels
        self.delete_tunnel = self.tunnels.delete_tunnel
        self.update_tunnel_status = self.tunnels.update_tunnel_status
        self.get_tunnel_stats = self.tunnels.get_tunnel_stats
        self.register_data_transfer = self.tunnels.register_data_transfer
        self.get_tunnel_metrics = self.tunnels.get_tunnel_metrics
        self.evaluate_tunnel_entropy = self.tunnels.evaluate_tunnel_entropy
        self.set_connection_check_policy = self.tunnels.set_connection_check_policy
        self.check_tunnels_health = self.tunnels.check_tunnels_health
        self.activate_tunnel = self.tunnels.activate_tunnel
        self.set_activating_status = self.tunnels.set_activating_status
        self.deactivate_tunnel = self.tunnels.deactivate_tunnel
        self.set_tunnel_technique = self.tunnels.set_tunnel_technique
        self.process_implant_beacon = self.tunnels.process_implant_beacon

        # Proxy methods from ImplantsUseCase
        self.create_implant = self.implants.create_implant
        self.list_implants = self.implants.list_implants
        self.get_implant = self.implants.get_implant
        self.delete_implant = self.implants.delete_implant
        self.generate_payload = self.implants.generate_payload

    def list_available_functions(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all available functions in this API with their docstrings and signatures.
        Designed for LLM consumption.
        """
        functions = []
        # Methods to exclude from discovery
        exclude = ['list_available_functions', 'tunnels', 'implants']
        
        for name in dir(self):
            if name.startswith('_') or name in exclude:
                continue
            
            attr = getattr(self, name)
            if callable(attr):
                doc = inspect.getdoc(attr) or "No documentation available."
                sig = str(inspect.signature(attr))
                functions.append({
                    "name": name,
                    "signature": sig,
                    "description": doc.split('\n')[0] # First line of docstring
                })
        return functions

def get_tunnels_api(dao=None):
    """
    Factory function to get an instance of TunnelsManagerAPI.
    """
    if dao is None:
        dao = GenericDAO()
    
    tunnels_repo = DatabaseTunnelRepository(dao)
    implants_repo = DatabaseImplantRepository(dao)
    connection_tester = NetworkConnectionTester()
    
    tunnels_usecase = TunnelsUseCase(tunnels_repo, connection_tester)
    implants_usecase = ImplantsUseCase(implants_repo)
    
    return TunnelsManagerAPI(tunnels_usecase, implants_usecase)
