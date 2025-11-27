from asciimatics.widgets import Frame, Layout, Label, ListBox, Divider, TextBox
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import StopApplication
from asciimatics.scene import Scene

# Datos simulados
ip_data = [
    ("192.168.1", "172.16.1", ["SMB", "FTP", "SSH"]),
    ("10.0.0.5", "172.16.1", ["HTTP", "DNS"]),
    ("192.168.2", "172.16.2", ["RDP", "Telnet"]),
    ("10.0.0.6", "172.16.2", ["SMTP", "POP3"]),
]

class IPFrame(Frame):
    def __init__(self, screen):
        super(IPFrame, self).__init__(screen, 30, screen.width, has_border=True, name="IP Selector")
        self.selected_index = 0
        self.protocols_visible = False
        self.expanded_mode = False

        layout = Layout([1])
        self.add_layout(layout)
        layout.add_widget(Label("Selecciona una IP (CTRL+O para ver protocolos, CTRL+OI para expandir)"))
        layout.add_widget(Divider())
        layout_body = Layout([1, 1])
        self.add_layout(layout_body)
        self.ip_list = ListBox(
            height=4,
            options=[(ip,idx) for idx,(ip,parent,_) in enumerate(ip_data)], # [(f"{ip} {parent}", i) for i, (ip, parent, _) in enumerate(ip_data)],
            name="ip_list",
            add_scroll_bar=True,
            on_change=self._on_select
        )
        self.parent_list = ListBox(
            height=4,
            options=[(parent,idx) for idx,(ip,parent,_) in enumerate(ip_data)], # [(f"{ip} {parent}", i) for i, (ip, parent, _) in enumerate(ip_data)],
            name="ip_list",
            add_scroll_bar=True,
            on_change=self._on_select
        )
        layout_body.add_widget(self.ip_list,column=0)
        layout_body.add_widget(self.parent_list,column=1)
        self.protocol_list = ListBox(
        height=3, # Usamos la altura ajustada previamente
        options=[], # Inicialmente vacío
        name="protocol_list",
        add_scroll_bar=True,
        on_change=self._on_protocol_select, # Nueva función para manejar la selección
        
        )
        layout_body.add_widget(self.protocol_list)    
        self.protocol_list.disabled = True
        self.protocol_list.custom_colour = "field"

        self.fix()
    def _on_protocol_select(self):
        if not self.protocols_visible:
            return  # No hacer nada si la lista de protocolos no está visible
        selected_protocol_index = self.protocol_list.value
        
        # Lógica para mostrar los detalles del protocolo
        # Ejemplo: Si el protocolo es "SMB", cargar y mostrar su información detallada
        
        # En un entorno TUI de asciimatics, esto generalmente implicaría:
        # 1. Obtener la referencia al protocolo seleccionado.
        # 2. Reemplazar la escena actual o el contenido del Frame con la vista de detalles.
        pass # Reemplazar con lógica de TUI avanzada
    def _on_select(self):
        self.selected_index = self.ip_list.value
        ip, parent, protocols = ip_data[self.selected_index]
        
        # Actualizar la lista de protocolos
        if self.protocols_visible:
            protocol_options = [(protocol, i) for i, protocol in enumerate(protocols)]
            self.protocol_list.options = protocol_options
            self.protocol_list.value = 0 # Seleccionar el primer protocolo por defecto

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('O'), ord('o')]:
                if self.protocols_visible:
                    self.protocol_list.options = []
                    self.protocols_visible = False
                else:
                    ip, parent, protocols = ip_data[self.selected_index]
                    self.protocol_list.options = [(protocol, i) for i, protocol in enumerate(protocols)]    
                    self.protocols_visible = True
                    

            elif event.key_code in [ord("I"),ord('i')]:  # CTRL+I (expandir)
                ...
            elif event.key_code in [ord('Q'), ord('q')]:
                raise StopApplication("Exit")
        return super(IPFrame, self).process_event(event)


def demo(screen):
    frame = IPFrame(screen)
    scene = Scene([frame], -1)
    screen.play([scene], stop_on_resize=True)
if __name__ == "__main__":
    try:
        Screen.wrapper(demo)
    except KeyboardInterrupt:
        exit(0)