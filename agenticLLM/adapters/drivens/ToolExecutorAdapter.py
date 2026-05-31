import json
import os
from typing import List, Dict, Any
from agenticLLM.models.agent import Tool
from agenticLLM.ports.drivens.forLLMAndTools import ForToolExecution
from tunnelsManager import TunnelsManagerAPI

from agenticLLM.core.agent_logger import get_logger

class SystemToolExecutorAdapter(ForToolExecution):
    def __init__(self, tunnels_api: TunnelsManagerAPI, generic_model=None, skills_registry=None):
        self.logger = get_logger()
        self.tunnels_api = tunnels_api
        self.generic_model = generic_model
        self.skills_registry = skills_registry
        self._tools_cache = []
        self._build_tools_cache()

    def _build_tools_cache(self):
        # 1. Tunnels Tools (Category: discovery)
        api_funcs = self.tunnels_api.list_available_functions()
        for func in api_funcs:
            # Sensitive tools disabled for now
            self._tools_cache.append(Tool(
                name=f"tunnels_{func['name']}",
                description=func['description'],
                parameters={},
                requires_approval=False,
                category="discovery"
            ))
        
        # 2. Database & OpSec Tools (Category: analysis)
        self._tools_cache.append(Tool(
            name="get_network_topology",
            description="Returns a list of all IPs and their discovered services.",
            parameters={},
            category="discovery"
        ))
        self._tools_cache.append(Tool(
            name="get_ip_opsec_analysis",
            description="Returns OpSec score, risk assessment, and suggestions for a specific IP.",
            parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]},
            category="analysis"
        ))
        self._tools_cache.append(Tool(
            name="get_artifacts",
            description="Lists all security artifacts registered for a specific IP.",
            parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]},
            category="analysis"
        ))
        self._tools_cache.append(Tool(
            name="search_techniques",
            description="Searches for MITRE ATT&CK techniques or command templates by keyword.",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            category="methodology"
        ))
        self._tools_cache.append(Tool(
            name="add_to_operational_memory",
            description="Saves a discovery or finding to the operation's context (RAG).",
            parameters={"type": "object", "properties": {"content": {"type": "string"}}, "required": ["content"]},
            category="general"
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
            },
            category="analysis"
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
            },
            category="analysis"
        ))
        self._tools_cache.append(Tool(
            name="get_cyber_kill_chain_status",
            description="Returns the current Cyber Kill Chain phase for a specific IP and its history.",
            parameters={"type": "object", "properties": {"ip": {"type": "string"}}, "required": ["ip"]},
            category="methodology"
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
            },
            category="methodology"
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
            requires_approval=False,
            category="discovery"
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
            },
            category="discovery"
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
            },
            category="analysis"
        ))

        # 6. Orchestration Tools
        self._tools_cache.append(Tool(
            name="get_available_agents",
            description="Lists all specialized agent personas (e.g., osint, maldev) and currently active agent sessions.",
            parameters={},
            category="orchestration"
        ))
        self._tools_cache.append(Tool(
            name="delegate_to_agent",
            description="Delegates a specific sub-task to a specialized agent. Use 'get_available_agents' first to find valid personas.",
            parameters={
                "type": "object", 
                "properties": {
                    "agent_persona": {"type": "string", "description": "The persona/type of the specialist (e.g., osint, maldev, opsec)"},
                    "task_description": {"type": "string"}
                },
                "required": ["agent_persona", "task_description"]
            },
            requires_approval=False,
            category="orchestration"
        ))

        self._tools_cache.append(Tool(
            name="create_custom_tool",
            description="Dynamically creates and registers a new tool in the system.",
            parameters={
                "type": "object", 
                "properties": {
                    "name": {"type": "string", "description": "Unique name for the tool"},
                    "description": {"type": "string"},
                    "parameters_schema": {"type": "object", "description": "JSON Schema for the tool parameters"},
                    "script_type": {"type": "string", "enum": ["python", "powershell", "cmd", "bash"], "default": "python"},
                    "code": {"type": "string", "description": "The logic/code for the tool"},
                    "requires_approval": {"type": "boolean", "default": True}
                },
                "required": ["name", "description", "parameters_schema", "code"]
            },
            requires_approval=False,
            category="development"
        ))

        # 7. Load existing custom tools from disk
        self._load_custom_tools_from_disk()

        # 5. Dynamic Skills
        if self.skills_registry:
            skills = self.skills_registry.list_available_skills()
            for skill in skills:
                self._tools_cache.append(Tool(
                    name=f"skill_{skill.name}",
                    description=f"{skill.description} Usage: {skill.usage_example}",
                    parameters=skill.parameters_schema or {"type": "object", "properties": {}},
                    requires_approval=skill.requires_approval,
                    category="general" # Skills are generally utility
                ))

    def list_tools(self, persona: str = "default") -> List[Tool]:
        """Returns a list of tools available for a specific persona."""
        persona_map = {
            "default": ["orchestration", "general"],
            "orchestrator": ["orchestration", "general"],
            "osint": ["discovery", "general", "orchestration"],
            "maldev": ["exploitation", "general", "orchestration"],
            "opsec": ["analysis", "general", "orchestration"],
            "kill_chain": ["methodology", "general", "orchestration"],
            "tool_creator": ["development", "general", "orchestration"]
        }
        
        allowed_categories = persona_map.get(persona, ["general", "orchestration"])
        return [t for t in self._tools_cache if t.category in allowed_categories]

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

    def _load_custom_tools_from_disk(self):
        """Loads and registers custom tools from the custom_tools directory."""
        custom_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "custom_tools")
        if not os.path.exists(custom_dir):
            return

        for filename in os.listdir(custom_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(custom_dir, filename), 'r', encoding='utf-8') as f:
                        tool_data = json.load(f)
                        # FORCE autonomous execution for now
                        tool_data["requires_approval"] = False
                        self._tools_cache.append(Tool.from_dict(tool_data))
                except Exception as e:
                    self.logger.error(f"Error loading custom tool {filename}: {e}")

    def _sanitize_name(self, name: str) -> str:
        """Sanitizes a tool name for use as a filename and identifier."""
        import re
        import unicodedata
        # Remove accents
        name = "".join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
        # Lowercase, replace spaces with underscores, remove non-alphanumeric
        name = name.lower().replace(" ", "_")
        name = re.sub(r'[^a-z0-9_]', '', name)
        return name

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        # Sanitize incoming name to ensure match with disk/cache
        safe_name = self._sanitize_name(name)
        self.logger.info(f"Executing tool: {name} (safe_name: {safe_name}) with args: {arguments}")

        # 1. Handle Custom Dynamic Tools (Python, PS1, CMD, SH)
        custom_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "custom_tools")
        json_file = os.path.join(custom_dir, f"{safe_name}.json")
        
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    tool_meta = json.load(f)
                
                stype = tool_meta.get("script_type", "python")
                self.logger.debug(f"Detected custom tool type: {stype}")
                
                # Execution Logic based on type
                if stype == "python":
                    python_file = os.path.join(custom_dir, f"{safe_name}.py")
                    import io
                    from contextlib import redirect_stdout
                    
                    f_stdout = io.StringIO()
                    # Prepare a rich execution context
                    ctx = {
                        "arguments": arguments, 
                        "generic_model": self.generic_model, 
                        "tunnels_api": self.tunnels_api, 
                        "result": None,
                        "print": print 
                    }
                    initial_keys = set(ctx.keys())
                    
                    try:
                        with open(python_file, 'r', encoding='utf-8') as f:
                            code_str = f.read()
                            with redirect_stdout(f_stdout):
                                exec(code_str, ctx)
                    except Exception as exec_e:
                        error_msg = f"Python Execution Error in '{safe_name}':\n{str(exec_e)}\n\nOutput before error:\n{f_stdout.getvalue()}"
                        self.logger.error(error_msg)
                        return error_msg
                    
                    res_var = ctx.get("result")
                    stdout_val = f_stdout.getvalue().strip()

                    # IF NO RESULT/STDOUT: Try to find a function to call automatically
                    if res_var is None and not stdout_val:
                        new_keys = set(ctx.keys()) - initial_keys
                        callables = {k: ctx[k] for k in new_keys if callable(ctx[k])}
                        
                        target_func = None
                        # Priority 1: Function name matches tool name
                        if safe_name in callables:
                            target_func = callables[safe_name]
                        # Priority 2: Exactly one function defined
                        elif len(callables) == 1:
                            target_func = list(callables.values())[0]
                        # Priority 3: Function named 'main'
                        elif "main" in callables:
                            target_func = callables["main"]
                        
                        if target_func:
                            self.logger.info(f"Auto-detecting function to call: {target_func.__name__}")
                            try:
                                # Try calling with keyword arguments from the tool call
                                res_var = target_func(**arguments)
                            except TypeError:
                                # Fallback: try calling without arguments
                                try:
                                    res_var = target_func()
                                except Exception as e:
                                    self.logger.error(f"Error calling detected function {target_func.__name__}: {e}")
                            
                    self.logger.info(f"result: {res_var}  {stdout_val}")
                    final_res = ""
                    if res_var is not None:
                        final_res = str(res_var)
                    elif stdout_val:
                        final_res = stdout_val
                    else:
                        final_res = f"Tool '{safe_name}' executed successfully (no return value or print output)."
                    
                    self.logger.info(f"Custom Python tool result: {final_res}")
                    return final_res
                
                else:
                    import subprocess
                    ext_map = {"powershell": "ps1", "cmd": "cmd", "bash": "sh"}
                    script_file = os.path.join(custom_dir, f"{safe_name}.{ext_map.get(stype)}")
                    
                    if not os.path.exists(script_file):
                        err = f"Error: Script file for '{safe_name}' ({stype}) not found at {script_file}."
                        self.logger.error(err)
                        return err
                    
                    # Prepare command environment
                    env = os.environ.copy()
                    env["TOOL_ARGS"] = json.dumps(arguments)
                    
                    if stype == "powershell":
                        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_file]
                    elif stype == "cmd":
                        cmd = ["cmd.exe", "/c", script_file]
                    else: # bash
                        cmd = ["bash", script_file]
                    
                    self.logger.debug(f"Running subprocess: {cmd}")
                    res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
                    
                    combined = f"[STDOUT]\n{res.stdout}\n[STDERR]\n{res.stderr}"
                    self.logger.info(f"Custom Shell tool result (exit code {res.returncode})")
                    return combined

            except Exception as e:
                err_msg = f"Internal Error executing custom tool {safe_name}: {str(e)}"
                self.logger.error(err_msg)
                return err_msg

        # 2. Handle Skills
        if name.startswith("skill_") or safe_name.startswith("skill_"):
            # Original name might be needed for registry lookup if not sanitized there
            skill_name = name.replace("skill_", "").replace("skill_", "") # twice just in case
            # Try registry with both
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

        elif name == "get_available_agents":
            if not self.generic_model or not self.generic_model.agent_manager:
                return "Agent Manager not available."
            
            manager = self.generic_model.agent_manager
            # Get possible personas from PromptManager via the manager
            personas = manager.prompt_manager.list_keys()
            # Get currently active instances
            active_sessions = manager.list_agents()
            
            return json.dumps({
                "available_personas": personas,
                "active_agent_sessions": active_sessions,
                "note": "You can delegate tasks to any persona using 'delegate_to_agent'."
            }, indent=2)

        elif name == "delegate_to_agent":
            agent_persona = arguments.get("agent_persona")
            task = arguments.get("task_description")
            if not agent_persona or not task: return "Missing agent_persona or task_description."
            
            if not self.generic_model or not self.generic_model.agent_manager:
                return "Agent Manager not available."
            
            # Use a unique name for the temporary specialized agent session
            agent_name = f"orchestrated_{agent_persona}"
            target_agent = self.generic_model.agent_manager.get_agent(agent_name)
            if not target_agent:
                target_agent = self.generic_model.agent_manager.create_agent(agent_name, persona=agent_persona)
            
            # Reset the specialized agent to ensure it starts with a clean history for the new task
            target_agent.reset()
            
            try:
                # Execute the task through the specialized agent
                response = target_agent.ask(task)
                return f"""
[DELEGATION REPORT FROM {agent_persona.upper()}]
STATUS: COMPLETED
FINDINGS:
{response}

INSTRUCTION FOR ORCHESTRATOR: Process these findings and decide on the next tactical step.
"""
            except Exception as e:
                return f"Error during delegation to {agent_persona}: {str(e)}"

        elif name == "create_custom_tool":
            raw_name = arguments.get("name")
            desc = arguments.get("description")
            schema = arguments.get("parameters_schema")
            # Support both 'code' and legacy 'python_code'
            code = arguments.get("code") or arguments.get("python_code")
            stype = arguments.get("script_type", "python")
            approval = arguments.get("requires_approval", False)
            
            if not all([raw_name, desc, schema, code]):
                return f"Missing required parameters for create_custom_tool. Received keys: {list(arguments.keys())}. Need: name, description, parameters_schema, code (or python_code)."
            
            # SANITIZE NAME: This ensures filenames and internal IDs are safe and matching
            tool_name = self._sanitize_name(raw_name)
            
            # Defensive: ensure schema is a dict
            if isinstance(schema, str):
                try:
                    schema = json.loads(schema)
                except:
                    return "Invalid JSON Schema provided in parameters_schema. Must be a valid JSON object/dict."

            try:
                # Ensure directory exists using absolute path
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                custom_dir = os.path.join(base_dir, "custom_tools")
                
                if not os.path.exists(custom_dir):
                    os.makedirs(custom_dir, exist_ok=True)
                
                # Save JSON definition
                tool_data = {
                    "name": tool_name,
                    "description": desc,
                    "parameters": schema,
                    "script_type": stype,
                    "requires_approval": approval
                }
                
                json_path = os.path.join(custom_dir, f"{tool_name}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(tool_data, f, indent=2, ensure_ascii=False)
                
                # Save actual script with correct extension
                ext_map = {"python": "py", "powershell": "ps1", "cmd": "cmd", "bash": "sh"}
                ext = ext_map.get(stype, "py")
                script_path = os.path.join(custom_dir, f"{tool_name}.{ext}")
                
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                
                # Add to current session cache (using the sanitized name)
                # Avoid duplicates in cache
                self._tools_cache = [t for t in self._tools_cache if t.name != tool_name]
                self._tools_cache.append(Tool.from_dict(tool_data))
                
                return f"SUCCESS: Custom tool '{tool_name}' ({stype}) created and registered successfully at {custom_dir}."
            except Exception as e:
                return f"FileSystem Error during tool creation: {str(e)}"

        return f"Tool {name} not found."
