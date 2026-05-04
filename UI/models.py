#from . import IPNode
from collections import defaultdict
from asciimatics.screen import Screen
class RepositoryModel:
    def __init__(self, repository):
        # repository can be a callable/class or an instance
        self.repository = repository() if callable(repository) else repository


class CommandModel:
    def __init__(self, commands):
        self.commands = commands

class Themes:
    PALETTES = {
        "dark": defaultdict(lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),{
            "background": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "label": (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "scroll": (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }),
        "light": defaultdict(lambda: (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),{
            "background": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "focus_field": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_YELLOW),
            "label": (Screen.COLOUR_BLUE, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "field": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "scroll": (Screen.COLOUR_MAGENTA, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "title": (Screen.COLOUR_RED, Screen.A_BOLD, Screen.COLOUR_WHITE),
            "disabled": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_WHITE),
        }),
        "hacker": defaultdict(lambda: (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),{
            "background": (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_GREEN),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "field": (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "scroll": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        })
    }


class UIMapper:
    """Convierte entidades IPNode y Ports en una lista de tuplas
    (ip_str, parent_ip_str, [protocols...]) para uso en la UI.

    Se puede inicializar vacío y luego cargar datos con `from_core` o
    pasando listas de entidades con `load(ips, ports)`.
    """
    def __init__(self, port_service_map: dict = None):
        self.port_service_map = port_service_map or {}
        self._value = []

    def load(self, ips, ports):
        """Construye la representación UI a partir de listas de entidades.

        ips: iterable de objetos IPNode (deben tener atributos .ip, .parent_ip y opcional .id)
        ports: iterable de objetos Port (deben tener atributos .port, .service_name y referencia a ip: .ip o .ip_id)
        """
        
        # mapas auxiliares
        ip_by_id = {}
        ip_by_ip = {}
        for ip in ips or []:
            if hasattr(ip, 'id'):
                ip_by_id[getattr(ip, 'id')] = ip
            ip_by_ip[getattr(ip, 'ip', None)] = ip

        protocols_by_ip = defaultdict(list)

        for p in ports or []:
            # resolver la entidad IP asociada al puerto
            ip_entity = None
            # varios posibles campos: ip (string), ip (int id), ip_id
            if hasattr(p, 'ip'):
                val = getattr(p, 'ip')
                ip_entity = ip_by_ip.get(val)

            if not ip_entity:
                # no podemos mapear este puerto a una IP conocida
                continue

            # determinar nombre del servicio/protocolo
            service = getattr(p, 'service_name', None)
            if not service:
                portnum = getattr(p, 'port', None)
                service = self.port_service_map.get(portnum, f'port_{portnum}')
            if ip_entity.ip:
                protocols_by_ip[ip_entity.ip].append(service)

        # construir la lista final
        result = []
        for ip in ips or []:
            ip_str = getattr(ip, 'ip', None)
            parent = getattr(ip, 'parent_ip', '')
            path = getattr(ip, 'path', '')
            child_level = getattr(ip, 'child_level', None)
            # fallback: algunos modelos usan 'path' para la carpeta
                
            protocols = protocols_by_ip.get(ip_str, [])
            result.append((ip_str, parent, protocols,child_level))#,path))

        self._value = result

    def from_core(self, core):
        """Cargar datos desde una instancia `core` que expone
        `select_all_ips()` y `select_all_ports()`.
        """
        ips = core.select_all_ips()
        ports = core.select_all_ports()
        print(ips,ports)
        self.load(ips, ports)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, data):
        # si se recibe una tupla/lista de (ips, ports)
        if isinstance(data, tuple) and len(data) == 2:
            self.load(data[0], data[1])
        else:
            # si se recibe una lista ya transformada
            self._value = data

def risk_color_for_score(score: float, low: float = 20.0, high: float = 65.0) -> str:
    """Map a noise score to a risk color: green (low), yellow (medium), red (high).
    
    Thresholds:
        score < low  → 'green'
        low <= score < high → 'yellow'
        score >= high → 'red'
    """
    if score >= high:
        return 'red'
    elif score >= low:
        return 'yellow'
    return 'green'


# --- Risk palette entries for asciimatics terminal colors ---

RISK_PALETTE_ENTRIES = {
    'risk_green': (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
    'risk_yellow': (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLACK),
    'risk_red': (Screen.COLOUR_RED, Screen.A_NORMAL, Screen.COLOUR_BLACK),
}


def inject_risk_palette(palette: dict) -> None:
    """Add risk_green, risk_yellow, risk_red entries to a Frame palette dict."""
    palette.update(RISK_PALETTE_ENTRIES)


def risk_colour_key_for_score(score: float, low: float = 20.0, high: float = 65.0) -> str:
    """Map a noise score to a risk palette key name for asciimatics custom_colour.
    
    Returns:
        'risk_green'  if score < low
        'risk_yellow' if low <= score < high
        'risk_red'    if score >= high
    """
    if score >= high:
        return 'risk_red'
    elif score >= low:
        return 'risk_yellow'
    return 'risk_green'


class Observer:
    """Base class for observers. Subclasses override observer_update(event_type, payload).
    
    Uses observer_update (not update) to avoid collision with
    asciimatics Effect.update(frame_no) in Frame subclasses.
    """
    def observer_update(self, event_type: str, payload: dict):
        """Called by Observable when an event occurs. Override in subclasses."""
        pass


class Observable:
    """Base class for observables with event_type + payload notification."""
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event_type: str, payload: dict):
        for observer in self._observers:
            observer.observer_update(event_type, payload)


class GenericModel(Observable):
    def __init__(self, repository, commands=None, port_service_map=None, ingestor=None, opsec_hooks=None, scoring_engine=None):
        super().__init__()
        self.repo = RepositoryModel(repository)
        self.cmd = CommandModel(commands)
        self.ingestor = ingestor
        self.mapper = UIMapper(port_service_map=port_service_map)
        self.scoring_engine = scoring_engine
        # Lazy import to avoid circular dependency
        if opsec_hooks is not None:
            self.opsec_hooks = opsec_hooks
        else:
            from hooks.opsec_hooks import OpSecHooks
            self.opsec_hooks = OpSecHooks()
        self._cachered = []
        self._just_parents = []
        self.protocols = ["SMB", "FTP", "SSH", "HTTP", "DNS", "RDP", "Telnet", "SMTP", "POP3", "IMAP", "LDAP", "SNMP"]
        self.themes = Themes.PALETTES
        self.current_theme = 'hacker'
        self._selected_ip = ''
        # campo usado para comunicarse con otros frames sobre la ip seleccionada
    @property
    def selected_ip(self):
        return self._selected_ip
    
    @selected_ip.setter
    def selected_ip(self, value):
        if self._selected_ip != value:
            self._selected_ip = value
            self.notify("selected_ip_changed", {"ip": value})
    @property
    def cachered_ips(self):
        if not self._cachered:
            ips = None
            ports = None
            repo = self.repo.repository
            # repository puede exponer select_all_ips/select_all_ports
            if hasattr(repo, 'select_all_ips'):
                ips = repo.select_all_ips()
            if hasattr(repo, 'select_all_ports'):
                ports = repo.select_all_ports()

            # si no hay ports disponibles pero el repo es en realidad un Core


            # cargar en el mapper
            self.mapper.load(ips or [], ports or [])
            self._cachered = self.mapper.value
        return self._cachered
    
    def reload_cache(self):
        """Fuerza la recarga del cache de IPs (util despues de importar logs)."""
        self._cachered = []
        return self.cachered_ips
    
    def get_all_actions(self):
        """
        Obtener todos los eventos/acciones registrados.
        
        Returns:
            Lista de entidades Actions si el repo lo soporta, None en otro caso
        """
        repo = self.repo.repository
        if hasattr(repo, 'select_all_actions'):
            return repo.select_all_actions()
        return None

    def get_operator_summary(self):
        """
        Obtener un resumen de acciones por operador.
        
        Returns:
            Dict: {operator_name: {'count': int, 'avg_noise': float, 'actions': list}}
        """
        actions = self.get_all_actions() or []
        summary = defaultdict(lambda: {'count': 0, 'total_noise': 0.0, 'actions': []})
        
        for act in actions:
            op = act.operator or "unknown"
            summary[op]['count'] += 1
            summary[op]['total_noise'] += act.noise_score or 0.0
            summary[op]['actions'].append(act)
            
        result = {}
        for op, data in summary.items():
            result[op] = {
                'count': data['count'],
                'avg_noise': data['total_noise'] / data['count'] if data['count'] > 0 else 0.0,
                'actions': data['actions']
            }
        return result
    @staticmethod
    def Quickshort(req:list[int]):
        fin = []
        if len(req) <= 1:
            return req
        
        pivot = req[-1]
        req.pop(req.index(pivot))    
        left = GenericModel.Quickshort([x for x in req if x <= pivot])
        right = GenericModel.Quickshort([x for x in req if x > pivot])
        fin.extend(left)
        fin.extend([pivot])
        fin.extend(right)
        return fin
    def split_ip(self, ip_str_lst:list[str]) -> list[int]:
        mp = {}
        for ip_str in ip_str_lst:
            lst = [int(octet) for octet in ip_str.split('.')]
            if lst[-1] in list(mp.keys()):
                ip_direction = mp[lst[-1]]
                ip_direction.append(lst)
                continue
                # [[192,168,1,5],[192,168,1,5],...] # si termina con el mismo key (que es el ultimo octeto)
            mp[lst[-1]] = [lst]
            organized_keys = GenericModel.Quickshort(list(mp.keys()))
        final_list = []
        for x in organized_keys:
            for ip in mp[x]:
                # print(f"Joining IP: {ip}")
                final_list.append('.'.join([ str(e) for e in ip ]))
        return final_list
    # es necesario crear un modelo
    # muy similar al que maneja la intefaz
    
    def get_suggestions_for_ip(self, ip):
        if self.ingestor:
            # Obtener puertos de la IP para buscar sugerencias relevantes
            ports = []
            for item in self.cachered_ips:
                if item[0] == ip:
                    ports = item[2]  # protocols
                    break
            # Buscar templates relacionados con los servicios o pivoting
            suggestions = []
            for service in ports:
                result = self.ingestor.searchCoincidence(service.lower())
                if result and result.templates:
                    suggestions.extend(result.templates)
            # Si no hay específicos, buscar generales de pivoting
        return [] or suggestions
    def get_generic_suggestions_for_ip(self,ip):
        suggestions = []
        result = self.ingestor.searchCoincidence("pivoting")
        if result and result.templates:
            suggestions.extend(result.templates)
        return suggestions
    
    def copy_to_clipboard(self, text):
        import subprocess
        try:
            # Usar clip.exe en Windows
            subprocess.run(['clip'], input=text, text=True, check=True)
        except Exception as e:
            # Fallback, intentar pyperclip si está instalado
            try:
                import pyperclip
                pyperclip.copy(text)
            except ImportError:
                pass  # No hacer nada si no se puede

    def _build_pivot_path(self, ip):
        """Build the pivot path (root → ... → leaf) from cachered_ips hierarchy."""
        # Build parent lookup: ip_str -> parent_ip_str
        parent_map = {}
        known_ips = set()
        for item in self.cachered_ips:
            ip_str = item[0]
            parent_ip = item[1]
            known_ips.add(ip_str)
            if parent_ip:
                parent_map[ip_str] = parent_ip

        if ip not in known_ips:
            return []

        # Walk up from ip to root
        path = [ip]
        current = ip
        visited = set()
        while current in parent_map and current not in visited:
            visited.add(current)
            parent = parent_map[current]
            if parent and parent in known_ips:
                path.append(parent)
                current = parent
            else:
                break

        path.reverse()  # root → ... → leaf
        return path

    def get_opsec_data(self, ip):
        """Return current OpSec data for an IP: noise_score, service, pivot_path, 
        risk_color, aggregate_noise, suggestions, status."""
        noise_score = 0
        service = None
        pivot_path = []
        status = "ok"
        aggregate_noise = {'total_noise': 0.0, 'per_ip': {}}
        suggestions = []
        try:
            # Get noise score from ScoringEngine if available
            if self.scoring_engine is not None:
                noise_score = self.scoring_engine.get_score(ip)

            # Get service from cachered_ips
            for item in self.cachered_ips:
                if item[0] == ip:
                    services = item[2]
                    if services:
                        service = services[0]
                    break

            # Build pivot path from hierarchy
            pivot_path = self._build_pivot_path(ip)

            # Get aggregate noise from ScoringEngine if available
            if self.scoring_engine is not None and pivot_path:
                aggregate_noise = self.scoring_engine.aggregate_pivot_noise(pivot_path)

            # Build suggestions from opsec_hooks
            if hasattr(self, 'opsec_hooks') and self.opsec_hooks:
                try:
                    noise_advice = self.opsec_hooks.on_noise_score_update(noise_score)
                    if noise_advice:
                        suggestions.append(noise_advice)
                except Exception:
                    pass
                try:
                    if service:
                        service_tips = self.opsec_hooks.on_service_selected(service)
                        if service_tips:
                            suggestions.extend(service_tips)
                except Exception:
                    pass
                try:
                    if pivot_path:
                        path_tips = self.opsec_hooks.on_pivot_path_change(pivot_path)
                        if path_tips:
                            suggestions.extend(path_tips)
                except Exception:
                    pass

        except Exception:
            status = "error"

        return {
            "noise_score": noise_score,
            "service": service,
            "pivot_path": pivot_path,
            "risk_color": risk_color_for_score(noise_score),
            "aggregate_noise": aggregate_noise,
            "suggestions": suggestions,
            "status": status,
        }
    

from collections import defaultdict
from asciimatics.screen import Screen

class TreeIPMapper:
    """
    Mapper especializado para TreeIPFrame que convierte entidades IPNode y Ports
    en una lista de tuplas jerárquicas:
    
    (ip_str, parent_ip_str, [protocols...], child_level)
    
    Mantiene la estructura padre-hijo ordenada por profundidad.
    """
    
    def __init__(self, port_service_map: dict = None):
        self.port_service_map = port_service_map or {}
        self._value = []
    
    def load(self, ips, ports):
        """
        Construye la representación jerárquica a partir de listas de entidades.
        
        ips: iterable de objetos IPNode (atributos: .ip, .parent_ip, .child_level)
        ports: iterable de objetos Port (atributos: .port, .service_name, .ip)
        """
        # mapas auxiliares para resolución rápida
        ip_by_id = {}
        ip_by_ip = {}
        for ip in ips or []:
            if hasattr(ip, 'id'):
                ip_by_id[getattr(ip, 'id')] = ip
            ip_by_ip[getattr(ip, 'ip', None)] = ip
        
        # mapear protocolos por IP
        protocols_by_ip = defaultdict(list)
        for p in ports or []:
            # resolver la entidad IP asociada al puerto
            ip_entity = None
            if hasattr(p, 'ip'):
                val = getattr(p, 'ip')
                # si es string, buscar directo; si es int, buscar por id
                if isinstance(val, str):
                    ip_entity = ip_by_ip.get(val)
                else:
                    ip_entity = ip_by_id.get(val)
            
            if not ip_entity:
                continue
            
            # determinar nombre del protocolo/servicio
            service = getattr(p, 'service_name', None)
            if not service:
                portnum = getattr(p, 'port', None)
                service = self.port_service_map.get(portnum, f'port_{portnum}')
            
            if ip_entity.ip:
                protocols_by_ip[ip_entity.ip].append(service)
        
        # construir la lista final manteniendo estructura jerárquica
        result = []
        for ip in ips or []:
            ip_str = getattr(ip, 'ip', None)
            parent = getattr(ip, 'parent_ip', '')
            child_level = getattr(ip, 'child_level', 0)
            protocols = protocols_by_ip.get(ip_str, [])
            
            result.append((ip_str, parent, protocols, child_level))
        
        # ordenar por child_level para garantizar estructura jerárquica correcta
        result.sort(key=lambda x: (x[3], x[0]))  # sort by child_level, then by ip
        self._value = result
    
    def from_core(self, core):
        """
        Cargar datos desde una instancia Core que expone
        select_all_ips() y select_all_ports().
        """
        ips = core.select_all_ips()
        ports = core.select_all_ports()
        self.load(ips, ports)
    
    def from_crud(self, crud):
        """
        Cargar datos desde una instancia CRUD_GATHERINGDB.
        """
        ips = crud.select_all_ips(dao=crud.dao)
        ports = crud.select_all_ports(dao=crud.dao)
        self.load(ips, ports)
    
    @property
    def value(self):
        """Retorna la lista de tuplas (ip, parent_ip, protocols, child_level)"""
        return self._value
    
    @value.setter
    def value(self, data):
        """Setter para cargar datos directamente"""
        if isinstance(data, tuple) and len(data) == 2:
            self.load(data[0], data[1])
        else:
            self._value = data


class GenericTreeModel:
    """
    Modelo genérico para TreeIPFrame que integra repository, commands y mapper.
    Similar a GenericModel pero optimizado para estructura jerárquica.
    """
    
    def __init__(self, repository=None, commands=None, port_service_map=None):
        self.repo = repository
        self.cmd = commands
        self.mapper = TreeIPMapper(port_service_map=port_service_map)
        self._cachered = []
        self.protocols = ["SMB", "FTP", "SSH", "HTTP", "DNS", "RDP", "Telnet", 
                         "SMTP", "POP3", "IMAP", "LDAP", "SNMP", "MySQL", "PostgreSQL"]
        self.current_theme = 'hacker'
        self.themes = {
            "dark": {
                "background": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
                "label": (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "scroll": (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "title": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
                "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
            },
            "light": {
                "background": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
                "focus_field": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_YELLOW),
                "label": (Screen.COLOUR_BLUE, Screen.A_NORMAL, Screen.COLOUR_WHITE),
                "field": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
                "scroll": (Screen.COLOUR_MAGENTA, Screen.A_NORMAL, Screen.COLOUR_WHITE),
                "title": (Screen.COLOUR_RED, Screen.A_BOLD, Screen.COLOUR_WHITE),
                "disabled": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_WHITE),
            },
            "hacker": {
                "background": (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_GREEN),
                "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
                "field": (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "scroll": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
                "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
                "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
            }
        }
    
    @property
    def cachered_ips(self):
        """Lazy-load y caché de datos desde repository"""
        if not self._cachered:
            if self.repo:
                # si repo tiene select_all_ips/select_all_ports (tipo Core o CRUD)
                if hasattr(self.repo, 'select_all_ips'):
                    ips = self.repo.select_all_ips()
                    ports = self.repo.select_all_ports() if hasattr(self.repo, 'select_all_ports') else []
                    self.mapper.load(ips, ports)
                    self._cachered = self.mapper.value
        return self._cachered
    
    def reload_from_core(self, core):
        """Recargar datos desde una instancia Core"""
        self.mapper.from_core(core)
        self._cachered = self.mapper.value
    
    def reload_from_crud(self, crud):
        """Recargar datos desde una instancia CRUD_GATHERINGDB"""
        self.mapper.from_crud(crud)
        self._cachered = self.mapper.value
    
    def get_suggestions_for_ip(self, ip):
        if self.ingestor:
            # Buscar templates relacionados con pivoting para la IP
            result = self.ingestor.searchCoincidence("pivoting")
        return result