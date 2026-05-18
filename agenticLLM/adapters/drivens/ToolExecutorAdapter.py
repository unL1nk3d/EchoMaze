import json
import os
from typing import List, Dict, Any
from agenticLLM.models.agent import Tool
from agenticLLM.ports.drivens.forLLMAndTools import ForToolExecution
from tunnelsManager import TunnelsManagerAPI

class SystemToolExecutorAdapter(ForToolExecution):
    def __init__(self, tunnels_api: TunnelsManagerAPI, generic_model=None, skills_registry=None):
        self.tunnels_api = tunnels_api
        self.generic_model = generic_model
        self.skills_registry = skills_registry
        self._tools_cache = []
        self._build_tools_cache()

    def _build_tools_cache(self):
        # 1. Tunnels Tools
        api_funcs = self.tunnels_api.list_available_functions()
        for func in api_funcs:
            # Sensitive tools require approval
            sensitive = ["delete_tunnel", "delete_implant"]
            self._tools_cache.append(Tool(
                name=f"tunnels_{func['name']}",
                description=func['description'],
                parameters={},
                requires_approval=func['name'] in sensitive
            ))
        
        # 2. Database & OpSec Tools (if generic_model is available)
        self._tools_cache.append(Tool(
            name="get_network_topology",
            description="Returns a list of all IPs and their discovered services.",
            parameters={}
        ))
        self._tools_cache.append(Tool(
            name="get_ip_opsec_analysis",
            description="Returns OpSec score, risk assessment, and suggestions for a specific IP.",
            parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
        ))
        self._tools_cache.append(Tool(
            name="get_artifacts",
            description="Lists all security artifacts registered for a specific IP.",
            parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
        ))
        self._tools_cache.append(Tool(
            name="search_techniques",
            description="Searches for MITRE ATT&CK techniques or command templates by keyword.",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        ))
        self._tools_cache.append(Tool(
            name="add_to_operational_memory",
            description="Saves a discovery or finding to the operation's context (RAG).",
            parameters={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]}
        ))
        self._tools_cache.append(Tool(
            name="register_action",
            description="Logs an administrative or offensive action performed by the agent. Affects noise score.",
            parameters={
                "type": "object", 
                "properties": {
                    "ip": {"type": "string"},
                    "command": {"type": "string"},
                    "noise_score": {"type": "number"}
                },
                "required": ["ip", "command"]
            }
        ))
        self._tools_cache.append(Tool(
            name="register_artifact",
            description="Registers a new file or artifact dropped/found on a target IP.",
            parameters={
                "type": "object", 
                "properties": {
                    "ip": {"type": "string"},
                    "filename": {"type": "string"},
                    "notes": {"type": "string"},
                    "noise_score": {"type": "number"}
                },
                "required": ["ip", "filename"]
            }
        ))
        self._tools_cache.append(Tool(
            name="get_cyber_kill_chain_status",
            description="Returns the current Cyber Kill Chain phase for a specific IP and its history.",
            parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]}
        ))
        self._tools_cache.append(Tool(
            name="set_cyber_kill_chain_phase",
            description="Updates the current Cyber Kill Chain phase for a specific target IP.",
            parameters={
                "type": "object", 
                "properties": {
                    "ip": {"type": "string"},
                    "phase": {
                        "type": "string", 
                        "enum": ["Reconnaissance", "Weaponization", "Delivery", "Exploitation", "Installation", "Command and Control", "Actions on Objectives"]
                    }
                },
                "required": ["ip", "phase"]
            }
        ))

        # 4. Active Pentesting Tools
        self._tools_cache.append(Tool(
            name="run_nmap_scan",
            description="Runs a real nmap scan on a target IP or network. Requires nmap installed on system.",
            parameters={
                "type": "object", 
                "properties": {
                    "target": {"type": "string", "description": "IP or network range (e.g. 192.168.1.1 or 192.168.1.0/24)"},
                    "arguments": {"type": "string", "description": "Nmap arguments (e.g. -sV -Pn)", "default": "-F"}
                },
                "required": ["target"]
            },
            requires_approval=True
        ))
        self._tools_cache.append(Tool(
            name="import_nmap_results",
            description="Imports results from an existing greppable nmap file (.gnmap).",
            parameters={
                "type": "object", 
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the .gnmap file"}
                },
                "required": ["filepath"]
            }
        ))
        self._tools_cache.append(Tool(
            name="get_tactical_advice",
            description="Get OpSec tactical advice for a specific service or noise level.",
            parameters={
                "type": "object", 
                "properties": {
                    "service": {"type": "string", "description": "Service name (e.g. smb, http)"},
                    "noise_score": {"type": "number", "description": "Current noise score"}
                }
            }
        ))

        # 5. Dynamic Skills
        if self.skills_registry:
            skills = self.skills_registry.list_available_skills()
            for skill in skills:
                self._tools_cache.append(Tool(
                    name=f"skill_{skill.name}",
                    description=f"{skill.description} Usage: {skill.usage_example}",
                    parameters=skill.parameters_schema or {"type": "object", "properties": {}},
                    requires_approval=skill.requires_approval
                ))

    def list_tools(self) -> List[Tool]:
        return self._tools_cache

    def load_tools_from_file(self, file_path: str):
        """Loads additional tools from a JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Tools file {file_path} not found.")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            self.load_tools_from_json(data)

    def load_tools_from_json(self, data: Any):
        """Loads additional tools from a list of tool dictionaries."""
        if isinstance(data, list):
            for tool_data in data:
                self._tools_cache.append(Tool.from_dict(tool_data))
        elif isinstance(data, dict):
             self._tools_cache.append(Tool.from_dict(data))

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        # Handle Skills
        if name.startswith("skill_") and self.skills_registry:
            skill_name = name.replace("skill_", "")
            return self.skills_registry.execute_skill(skill_name, arguments)

        # Handle Tunnels Tools
        if name.startswith("tunnels_"):
            func_name = name.replace("tunnels_", "")
            if hasattr(self.tunnels_api, func_name):
                func = getattr(self.tunnels_api, func_name)
                try:
                    result = func(**arguments)
                    return str(result)
                except Exception as e:
                    return f"Error executing {name}: {str(e)}"

        # Handle System/OpSec Tools
        if not self.generic_model:
            return "Generic model not initialized. System tools unavailable."

        if name == "get_network_topology":
            ips = self.generic_model.cachered_ips
            return json.dumps(ips, indent=2)

        elif name == "get_ip_opsec_analysis":
            ip = arguments.get("ip")
            if not ip: return "Missing IP argument."
            data = self.generic_model.get_opsec_data(ip)
            return json.dumps(data, indent=2)

        elif name == "get_artifacts":
            ip = arguments.get("ip")
            if not ip: return "Missing IP argument."
            artifacts = self.generic_model.get_artifacts_for_ip(ip)
            # Convert artifacts to dict for JSON serialization
            return json.dumps([vars(a) for a in artifacts], indent=2)
        
        elif name == "search_techniques":
            query = arguments.get("query")
            if not query: return "Missing query argument."
            if not self.generic_model.ingestor:
                return "Cheat Ingestor not available."
            result = self.generic_model.ingestor.searchCoincidence(query)
            if result and hasattr(result, 'templates'):
                return json.dumps([vars(t) for t in result.templates], indent=2)
            return f"No techniques found for '{query}'."

        elif name == "add_to_operational_memory":
            content = arguments.get("content")
            if not content: return "Missing content argument."
            if not hasattr(self.generic_model, 'agent_usecase') or not self.generic_model.agent_usecase:
                 return "Agent use case not linked."
            from agenticLLM.models.agent import OperationalMemory
            memory = OperationalMemory(content=content, source="agent_finding")
            self.generic_model.agent_usecase.memory_repo.save_memory(memory)
            return f"Finding saved to operational memory."

        elif name == "register_action":
            ip = arguments.get("ip")
            command = arguments.get("command")
            noise = arguments.get("noise_score", 0.0)
            if not ip or not command: return "Missing IP or command."
            success = self.generic_model.add_action(ip, "EchoAI_Agent", command, float(noise))
            return "Action registered and scored." if success else f"Failed to register action for {ip}."

        elif name == "register_artifact":
            ip = arguments.get("ip")
            filename = arguments.get("filename")
            notes = arguments.get("notes", "")
            noise = arguments.get("noise_score", 0.0)
            if not ip or not filename: return "Missing IP or filename."
            success = self.generic_model.add_artifact(ip, filename, notes, float(noise))
            return "Artifact registered and scored." if success else f"Failed to register artifact for {ip}."

        elif name == "get_cyber_kill_chain_status":
            ip = arguments.get("ip")
            if not ip: return "Missing IP argument."
            if not hasattr(self.generic_model, 'agent_usecase'): return "Agent not linked."
            memories = self.generic_model.agent_usecase.memory_repo.list_all_memories()
            # Find latest phase set for this IP in metadata
            current_phase = "Reconnaissance"
            history = []
            for m in memories:
                if m.metadata.get("target_ip") == ip and m.source == "kill_chain_update":
                    current_phase = m.phase
                    history.append(f"[{m.timestamp}] -> {m.phase}")
            
            return json.dumps({"ip": ip, "current_phase": current_phase, "history": history}, indent=2)

        elif name == "set_cyber_kill_chain_phase":
            ip = arguments.get("ip")
            phase = arguments.get("phase")
            if not ip or not phase: return "Missing IP or phase."
            if not hasattr(self.generic_model, 'agent_usecase'): return "Agent not linked."
            from agenticLLM.models.agent import OperationalMemory
            memory = OperationalMemory(
                content=f"Methodology Update: Target {ip} moved to phase {phase}.",
                source="kill_chain_update",
                phase=phase,
                metadata={"target_ip": ip}
            )
            self.generic_model.agent_usecase.memory_repo.save_memory(memory)
            return f"Cyber Kill Chain phase updated to {phase} for {ip}."
        
        elif name == "run_nmap_scan":
            target = arguments.get("target")
            args = arguments.get("arguments", "-F")
            if not target: return "Missing target IP or network."
            
            import subprocess
            output_file = f"nmap_{target.replace('/', '_')}.gnmap"
            full_command = f"nmap {args} -oG {output_file} {target}"
            
            try:
                # Run the scan
                process = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=300)
                if process.returncode != 0:
                    return f"Nmap scan failed: {process.stderr}"
                
                # Import the results automatically
                if self.generic_model.cmd and self.generic_model.cmd.commands:
                    self.generic_model.cmd.commands.import_from_nmap_scan_file(output_file)
                    return f"Scan completed and results imported from {output_file}.\nOutput Snippet: {process.stdout[:200]}..."
                return f"Scan completed but could not import results (Commands not linked)."
            except Exception as e:
                return f"Error running nmap: {str(e)}"

        elif name == "import_nmap_results":
            filepath = arguments.get("filepath")
            if not filepath: return "Missing filepath."
            if not os.path.exists(filepath): return f"File {filepath} not found."
            
            try:
                if self.generic_model.cmd and self.generic_model.cmd.commands:
                    results = self.generic_model.cmd.commands.import_from_nmap_scan_file(filepath)
                    return f"Successfully imported results for {len(results)} hosts from {filepath}."
                return "Commands not linked."
            except Exception as e:
                return f"Error importing results: {str(e)}"

        elif name == "get_tactical_advice":
            service = arguments.get("service")
            score = arguments.get("noise_score")
            
            advice = []
            repo = self.generic_model.repo.repository
            if hasattr(repo, 'tactical_suggestions'):
                ts = repo.tactical_suggestions
                if score is not None:
                    advice.append(ts.get_noise_advice(int(score)))
                if service:
                    advice.extend(ts.suggest_for_service(service))
                return "\n".join(advice) if advice else "No specific advice available for these parameters."
            return "Tactical suggestions engine not available."

        return f"Tool {name} not found."
