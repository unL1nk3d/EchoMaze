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
        self._selected_idx = 0
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

    def _build_tree(self):
        """Construir árbol jerárquico desde model.cachered_ips"""
        self._tree_nodes = []
        self._expanded = set()

        # Obtener IPs del modelo
        ips_data = self.model.cachered_ips  # lista de (ip, parent_ip, protocols, child_level)

        # Agrupar por nivel y jerarquía
        principal_ips = [item for item in ips_data if item[3] == 0]
        child_ips_map = {}
        for ip, parent_ip, protocols, child_level in ips_data:
            if child_level > 0:
                if parent_ip not in child_ips_map:
                    child_ips_map[parent_ip] = []
                child_ips_map[parent_ip].append((ip, protocols, child_level))

        # Construir árbol (estructura plana con indentación)
        for principal_ip, _, protocols, _ in principal_ips:
            # Nodo principal (siempre visible)
            self._tree_nodes.append({
                'type': 'principal',
                'ip': principal_ip,
                'protocols': protocols,
                'indent': 0,
                'parent': None,
                'children_key': principal_ip
            })

            # Nodos hijos (colapsables)
            if principal_ip in child_ips_map:
                for child_ip, child_protocols, child_level in child_ips_map[principal_ip]:
                    self._tree_nodes.append({
                        'type': 'child',
                        'ip': child_ip,
                        'protocols': child_protocols,
                        'indent': 1,
                        'parent': principal_ip,
                        'children_key': None
                    })

        # Actualizar ListBox
        self._update_tree_display()

    def _update_tree_display(self):
        """Actualizar visualización del árbol en la ListBox"""
        options = []
        for idx, node in enumerate(self._tree_nodes):
            if node['type'] == 'principal':
                # Mostrar con expansión visual
                icon = "▼" if node['children_key'] in self._expanded else "▶"
                display = f"{icon} {node['ip']}"
            else:  # child
                display = f"  └─ {node['ip']}"

            options.append((display, idx))

        self.tree_list.options = options

    def _on_tree_select(self):
        """Callback cuando se selecciona un nodo del árbol"""
        if self.tree_list.value is not None:
            self._selected_idx = self.tree_list.value
            node = self._tree_nodes[self._selected_idx]

            # Mostrar detalles
            self._show_node_details(node)

            # Mostrar protocolos
            if node['protocols']:
                self.protocol_list.options = [(p, i) for i, p in enumerate(node['protocols'])]
            else:
                self.protocol_list.options = []

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

    def _toggle_node_expansion(self):
        """Expandir/Contraer nodo seleccionado - añade/elimina dinámicamente nodos hijos"""
        if self._selected_idx >= len(self._tree_nodes):
            return

        node = self._tree_nodes[self._selected_idx]
        if node['type'] != 'principal':
            return  # Solo se pueden expandir nodos principales

        if node['children_key'] in self._expanded:
            # Contraer: eliminar dinámicamente nodos hijos
            self._remove_child_nodes(node['children_key'])
            self._expanded.discard(node['children_key'])
            self._update_status(f"[-] Collapsed: {node['ip']}")
        else:
            # Expandir: añadir dinámicamente nodos hijos
            self._remove_child_nodes(node['children_key'])  # Asegurar que no haya duplicados
            self._add_child_nodes(self._selected_idx + 1, node['children_key'])
            self._expanded.add(node['children_key'])
            self._update_status(f"[+] Expanded: {node['ip']}")

        self._update_tree_display()

    def _add_child_nodes(self, insert_idx, parent_ip):
        """Añadir dinámicamente nodos hijos en la posición correcta"""
        # Obtener las IPs hijas del modelo
        ips_data = self.model.cachered_ips
        child_ips = [(ip, protocols, child_level) for ip, p, protocols, child_level in ips_data 
                     if p == parent_ip and child_level > 0]

        # Insertar nodos hijos después del nodo padre
        for idx, (child_ip, child_protocols, child_level) in enumerate(child_ips):
            child_node = {
                'type': 'child',
                'ip': child_ip,
                'protocols': child_protocols,
                'indent': 1,
                'parent': parent_ip,
                'children_key': None
            }
            self._tree_nodes.insert(insert_idx + idx, child_node)

    def _remove_child_nodes(self, parent_ip):
        """Eliminar dinámicamente todos los nodos hijos de un padre"""
        # Encontrar y eliminar todos los nodos hijos (de atrás hacia adelante para evitar problemas de índice)
        indices_to_remove = []
        for idx, node in enumerate(self._tree_nodes):
            if node['type'] == 'child' and node['parent'] == parent_ip:
                indices_to_remove.append(idx)

        # Eliminar de atrás hacia adelante
        for idx in sorted(indices_to_remove, reverse=True):
            self._tree_nodes.pop(idx)
            # Ajustar índice seleccionado si es necesario
            if self._selected_idx > idx:
                self._selected_idx -= 1

    def _update_status(self, message):
        """Actualizar etiqueta de estado"""
        self.status_label.text = message

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
            #elif event.key_code == Screen.KEY_LEFT:
            #    # Contraer
            #    if self._selected_idx < len(self._tree_nodes):
            #        node = self._tree_nodes[self._selected_idx]
            #        if node['type'] == 'principal' and node['children_key'] in self._expanded:
            #            self._expanded.discard(node['children_key'])
            #            self._update_tree_display()
            #            self._update_status(f"[-] Collapsed: {node['ip']}")
            elif event.key_code in [ord('I'), ord('i')]:
                raise NextScene("protocols")
            elif event.key_code in [ord('S'), ord('s')]:
                raise NextScene("search")

        return super(TreeIPFrame, self).process_event(event)


def demo(screen, old_scene):
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
        ('192.168.1.102', '192.168.1.102', ['redis'], 2),
        
        ('10.0.0.1', '', ['https', 'dns'], 0),
        ('10.0.0.50', '10.0.0.1', ['ldap'], 1),
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