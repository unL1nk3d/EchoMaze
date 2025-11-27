#!/usr/bin/env python3

from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, Widget, Label, PopUpDialog, Text, Divider, ListBox
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication, NextScene
from asciimatics.scene import Scene
import sys


class TreeIPFrame(Frame):
    """
    Frame que muestra una estructura de árbol jerárquica de IPs:
    - Raíz: IPs principales (child_level == 0)
      └─ Hijos: IPs hijas (child_level > 0)
         └─ Protocolos/Puertos asociados
    
    Integra:
    - Core: para parsear y recargar desde directorios
    - Main (CRUD): para acceder a la BD
    - Models: GenericModel con mapper y temas
    """

    PALETTES = {
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

    def __init__(self, screen, model, core=None, theme="hacker"):
        """
        :param screen: asciimatics Screen
        :param model: GenericModel con repo, cmd, mapper, temas
        :param core: Core instance para operaciones de reload/parse
        :param theme: nombre del tema inicial
        """
        super(TreeIPFrame, self).__init__(
            screen, screen.height, screen.width,
            has_border=True,
            name="IP Tree Manager",
            #palette=self.PALETTES.get(theme, self.PALETTES["hacker"])
        )
        self.model = model
        self.core = core
        self.current_theme = theme
        self._tree_nodes = []  # lista de nodos del árbol (representación plana)
        self._expanded = set()  # set de índices expandidos
        self.__selected_idx = 0
        self._expand_depths = {}  # mapa parent_ip -> depth de expansión (0 = colapsado)
        self._visible_nodes = []  # lista paralela a tree_list.options con nodos visibles
        self.set_theme('bright')

        # ========== LAYOUT HEADER ==========
        layout_header = Layout([1], fill_frame=False)
        self.add_layout(layout_header)
        layout_header.add_widget(Label("=== IP Hierarchy Tree Browser ==="))
        layout_header.add_widget(Label("↑/↓: Navigate | →: Expand | ←: Collapse | R: Reload | T: Theme | Q: Quit"))
        layout_header.add_widget(Divider())

        # ========== LAYOUT MAIN (3 columnas) ==========
        layout_body = Layout([2], fill_frame=True)
        layout_ip_details = Layout([1,1,1], fill_frame=False)
        layout_spans = Layout([1], fill_frame=False)
        layout_port_info_details = Layout([1,1], fill_frame=False)
        self.add_layout(layout_ip_details)
        self.add_layout(layout_spans)
        self.add_layout(layout_body)
        self.add_layout(layout_port_info_details)
        

        # Columna 1: Árbol (más ancho)
        layout_body.add_widget(Label("IP Tree (Expandable)"), column=0)
        self.tree_list = ListBox(
            height=Widget.FILL_COLUMN,#Widget.FILL_FRAME,
            options=[],
            name="tree_list",
            add_scroll_bar=True,
            on_change=self._on_tree_select
        )
        layout_body.add_widget(self.tree_list, column=0)

        # Columna 2: Detalles de IP seleccionada

        
        layout_ip_details.add_widget(Label("IP Details"), column=0)
        self.details_text = Text(
            #height=Widget.FILL_FRAME,
            #as_string=True,
            disabled=True,
            name="details"
        )
        self.details_parent = Text(
            disabled=True,
            name="parent"
        )
        self.details_ports = Text(
            disabled=True,
            name="ports"
        )
        layout_port_info_details.add_widget(Label("Protocols"), column=0)
        layout_port_info_details.add_widget(self.details_ports, column=0)
        layout_ip_details.add_widget(self.details_text, column=0)
        
        layout_ip_details.add_widget(Label("Parent IP"), column=1)
        layout_ip_details.add_widget(self.details_parent, column=1)
        # Columna 3: Protocolos/Puertos
        #layout_ip_details.add_widget(Label("Protocols"), column=2)
        self.protocol_list = ListBox(
            height=Widget.FILL_COLUMN,#Widget.FILL_FRAME,
            options=[],
            name="protocols",
            add_scroll_bar=True
        )
        
        layout_spans.add_widget(Divider(), column=0)
        layout_port_info_details.add_widget(self.protocol_list, column=1)

        # ========== LAYOUT FOOTER ==========
        layout_footer = Layout([1], fill_frame=False)
        self.add_layout(layout_footer)
        layout_footer.add_widget(Divider())
        self.status_label = Label("")
        layout_footer.add_widget(self.status_label,column=0)

        self.fix()
        self._build_tree()
    @property
    def _selected_idx(self):
        return self.__selected_idx
    @_selected_idx.setter
    def _selected_idx(self,arg:int):
        self.__selected_idx = arg
        self.model.selected_ip = self._visible_nodes[arg]['ip']
    
    def _build_tree(self):
        """Construir representación jerárquica base desde model.cachered_ips"""
        # Construir mapa padre -> hijos para consultas rápidas
        ips_data = self.model.cachered_ips  # lista de (ip, parent_ip, protocols, child_level)
        self._children_map = {}
        self._principals = []
        for ip, parent_ip, protocols, child_level in ips_data:
            if child_level == 0:
                self._principals.append((ip, protocols))
            else:
                self._children_map.setdefault(parent_ip, []).append((ip, protocols, child_level))

        # Garantizar que todo principal tiene un depth (por defecto 0)
        for principal, _ in self._principals:
            self._expand_depths.setdefault(principal, 0)

        # Reconstruir visual según depths actuales
        self._update_tree_display()

    def _gather_children(self, parent_ip, max_depth, current_depth=1):
        """
        Recursivamente recolección de hijos hasta max_depth.
        Devuelve lista de dicts: {'type','ip','protocols','indent','parent'}
        """
        if max_depth < 1:
            return []
        nodes = []
        children = self._children_map.get(parent_ip, [])
        for ip, protocols, child_level in children:
            nodes.append({
                'type': 'child',
                'ip': ip,
                'protocols': protocols,
                'indent': current_depth,
                'parent': parent_ip
            })
            # Recursión para hijos de hijos
            nodes.extend(self._gather_children(ip, max_depth - 1, current_depth + 1))
        return nodes

    def _update_tree_display(self):
        """Actualizar visualización del árbol en la ListBox según self._expand_depths"""
        options = []
        visible_nodes = []
        for principal_ip, protocols in self._principals:
            depth = self._expand_depths.get(principal_ip, 0)
            icon = "▼" if depth > 0 else "▶"
            # Mostrar icono de expandir/contraer. Si es la fila seleccionada, añadir marcador '→'
            display = f"{icon} {principal_ip}"
            options.append((display, len(visible_nodes)))
            visible_nodes.append({
                'type': 'principal',
                'ip': principal_ip,
                'protocols': protocols,
                'indent': 0,
                'parent': None
            })

            # Si depth > 0, añadir hijos recursivamente hasta depth
            if depth > 0:
                child_nodes = self._gather_children(principal_ip, depth, current_depth=1)
                for child in child_nodes:
                    indent_spaces = "  " * child['indent']
                    display = f"{indent_spaces}└─ {child['ip']}"
                    options.append((display, len(visible_nodes)))
                    visible_nodes.append(child)

        # Guardar mapa de visibles para callbacks
        self._visible_nodes = visible_nodes
        self.tree_list.options = options

        # Mantener selección en rango
        if self._selected_idx >= len(self._visible_nodes):
            self._selected_idx = max(0, len(self._visible_nodes) - 1)
        self.tree_list.value = self._selected_idx

        # Forzar redraw/re-layout para que ListBox muestre los cambios inmediatamente
        try:
            self.fix()
        except Exception:
            # defensivo: no queremos romper el flujo si fix falla por restricción de estado
            pass

    def _on_tree_select(self):
        """Callback cuando se selecciona un nodo del árbol"""
        if self.tree_list.value is not None:
            self._selected_idx = self.tree_list.value
            node = self._visible_nodes[self._selected_idx]
            self._show_node_details(node)
            if node['protocols']:
                self.protocol_list.options = [(p, i) for i, p in enumerate(node['protocols'])]
            else:
                self.protocol_list.options = []

    def _toggle_node_expansion(self):
        """Alternar expansión del nodo principal seleccionado (0 <-> 1)"""
        if self._selected_idx >= len(self._visible_nodes):
            return
        node = self._visible_nodes[self._selected_idx]
        if node['type'] != 'principal':
            # Si es hijo, mover selección al padre principal (si existe)
            parent_ip = node.get('parent')
            if parent_ip:
                # encontrar índice del principal en visibles y seleccionarlo
                for idx, n in enumerate(self._visible_nodes):
                    if n['type'] == 'principal' and n['ip'] == parent_ip:
                        self._selected_idx = idx
                        break
                # ahora togglear
                node = self._visible_nodes[self._selected_idx]
            else:
                return

        parent_ip = node['ip']
        current = self._expand_depths.get(parent_ip, 0)
        # alternar entre 0 y 1 (si quieres comportamiento distinto ajustar aquí)
        self._expand_depths[parent_ip] = 0 if current > 0 else 1
        self._update_tree_display()
        self._update_status(f"[+] Depth for {parent_ip}: {self._expand_depths[parent_ip]}")

    def _increase_depth_selected(self, delta=1):
        """Aumentar profundidad de expansión para el principal seleccionado"""
        if self._selected_idx >= len(self._visible_nodes):
            return
        node = self._visible_nodes[self._selected_idx]
        # si es hijo, usar su padre principal
        if node['type'] == 'child':
            parent_ip = node.get('parent')
            # buscar índice del principal y usarlo
            for idx, n in enumerate(self._visible_nodes):
                if n['type'] == 'principal' and n['ip'] == parent_ip:
                    self._selected_idx = idx
                    node = self._visible_nodes[self._selected_idx]
                    break
        if node['type'] != 'principal':
            return
        parent_ip = node['ip']
        self._expand_depths[parent_ip] = self._expand_depths.get(parent_ip, 0) + delta
        # cap razonable a 5 para evitar expansiones incontroladas
        self._expand_depths[parent_ip] = min(5, self._expand_depths[parent_ip])
        self._update_tree_display()
        self._update_status(f"[+] Depth for {parent_ip}: {self._expand_depths[parent_ip]}")

    def _decrease_depth_selected(self, delta=1):
        """Disminuir profundidad de expansión para el principal seleccionado"""
        if self._selected_idx >= len(self._visible_nodes):
            return
        node = self._visible_nodes[self._selected_idx]
        if node['type'] == 'child':
            parent_ip = node.get('parent')
            for idx, n in enumerate(self._visible_nodes):
                if n['type'] == 'principal' and n['ip'] == parent_ip:
                    self._selected_idx = idx
                    node = self._visible_nodes[self._selected_idx]
                    break
        if node['type'] != 'principal':
            return
        parent_ip = node['ip']
        self._expand_depths[parent_ip] = max(0, self._expand_depths.get(parent_ip, 0) - delta)
        self._update_tree_display()
        self._update_status(f"[+] Depth for {parent_ip}: {self._expand_depths[parent_ip]}")

    def _show_node_details(self, node):
        """Mostrar detalles del nodo seleccionado"""
        details = f"IP: {node['ip']}\n"
        # details += f"Type: {node['type'].upper()}\n"
        if node['parent']:
            self.details_parent.value = f"Parent: {node['parent']}"
            #details += f"Parent: {node['parent']}\n"
        #details += f"Protocols: {len(node['protocols'])}\n"
        self.details_text.value = details
        
        details = ""
        if node['protocols']:
            details += f"Services: {', '.join(node['protocols'][:5])}"
            if len(node['protocols']) > 5:
                details += f"... +{len(node['protocols']) - 5} more"

        self.details_ports.value = details

    def reload_from_directory(self):
        """Recargar datos desde directorios usando Core"""
        self._update_status("[*] Reloading from directory...")

        try:
            if self.core and hasattr(self.core, 'insert_ip_from_directory'):
                # Llamar al core para parsear desde directorios
                self.core.insert_ip_from_directory('scan_results')
                self._update_status("[+] Core parsing complete")

            # Recargar mapper desde repositorio
            if hasattr(self.model.mapper, 'from_core') and self.model.repo:
                self.model.mapper.from_core(self.model.repo.repository)
                self._update_status("[+] Model updated from repository")

            # Limpiar caché y reconstruir árbol
            self.model._cachered = []
            self._build_tree()
            self._update_status("[+] Tree rebuilt successfully")

        except Exception as e:
            self._update_status(f"[-] Error reloading: {str(e)}")

    def change_theme(self):
        """Rotar entre temas disponibles"""
        themes = list(self.PALETTES.keys())
        current_idx = themes.index(self.current_theme)
        new_theme = themes[(current_idx + 1) % len(themes)]
        self.current_theme = new_theme
        self.palette = self.PALETTES[new_theme]
        self.fix()
        self._update_status(f"[+] Theme: {new_theme}")

    def process_event(self, event):
        """Procesar eventos de teclado"""
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('Q'), ord('q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code in [ord('R'), ord('r')]:
                self.reload_from_directory()
            elif event.key_code in [ord('T'), ord('t')]:
                self.change_theme()
            elif event.key_code == Screen.KEY_RIGHT:
                self._toggle_node_expansion()
            elif event.key_code == ord('+') or event.key_code == ord('='):
                # aumentar profundidad del principal seleccionado
                self._increase_depth_selected(1)
                self._update_tree_display()
            elif event.key_code == ord('-') or event.key_code == ord('_'):
                # disminuir profundidad
                self._decrease_depth_selected(1)
                self._update_tree_display()
            elif event.key_code in [ord('I'), ord('i')]:
                raise NextScene("protocols")
            elif event.key_code in [ord('S'), ord('s')]:
                raise NextScene("search")

        return super(TreeIPFrame, self).process_event(event)
    def _update_status(self, message):
        """Actualizar etiqueta de estado"""
        self.status_label.text = message

def demo(screen, old_scene):
# ...en la función demo()...
    # Crear modelo usando el nuevo mapper
    from UI.models import GenericTreeModel
    from core import Core
    from GATHERINGDB.main import CRUD_GATHERINGDB
    from GATHERINGDB.dao import GenericDAO


    try:
        dao = GenericDAO()
        crud = CRUD_GATHERINGDB(dao=dao)
        core = Core(crud=crud)
    except:
        core = None
    # Cargar datos explícitamente si es necesario
    model = GenericTreeModel(
        repository=core,  # o DemoRepo() para demo
        commands=None,
        port_service_map={}
    )
    if core:
        model.reload_from_core(core)
    else:
        # para demo, llenar manualmente como antes
        model._cachered = [
            ('192.168.1.1', '', ['http', 'ssh'], 0),
            ('192.168.1.100', '192.168.1.1', ['mysql'], 1),
            ('192.168.1.102', '192.168.1.100', ['redis'], 2),
            # ...
        ]
    
    screen.play(
        [Scene([TreeIPFrame(screen, model, core=core)], -1)],
        stop_on_resize=True,
        start_scene=old_scene
    )
def demo_mock(screen, old_scene):
    """Demo con modelo simulado"""
    from UI.models import GenericModel
    from core import Core
    from GATHERINGDB.main import CRUD_GATHERINGDB
    from GATHERINGDB.dao import GenericDAO

    # Crear instancias reales o simuladas
    try:
        dao = GenericDAO()
        crud = CRUD_GATHERINGDB(dao=dao)
        core = Core(crud=crud)
    except:
        core = None

    class DemoRepo:
        def select_all_ips(self):
            return []
        def select_all_ports(self):
            return []

    # Crear modelo
    model = GenericModel(
        repository=DemoRepo(),
        commands=None,
        port_service_map={}
    )
    # Llenar con datos de demo
    model._cachered = [
        ('192.168.1.1', '', ['http', 'ssh'], 0),
        ('192.188.1.1','',['http','ftp'],0),
        ('192.168.1.100', '192.168.1.1', ['mysql'], 1),
        ('192.168.1.101', '192.168.1.1', ['redis'], 1),
        ('192.168.1.101', '192.168.1.1', ['redis'], 1),
        ('192.168.1.102', '192.168.1.101', ['redis'], 2),
        
        ('10.0.0.1', '', ['https', 'dns'], 0),
        ('10.0.0.50', '10.0.0.1', ['ldap'], 1),
        ('10.0.0.51','10.0.0.1',['ldap'],1),
        ('0.0.0.0','10.0.0.51',['ntp'],2),
    ]

    screen.play(
        [Scene([TreeIPFrame(screen, model, core=core)], -1)],
        stop_on_resize=True,
        start_scene=old_scene
    )


if __name__ == '__main__':
    last_scene = None
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene