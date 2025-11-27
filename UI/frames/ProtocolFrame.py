
from asciimatics.widgets import Frame, Layout, Label, ListBox, Divider,TextBox
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import StopApplication, NextScene
from asciimatics.scene import Scene
class ProtocolFrame(Frame):
    def __init__(self, screen, model):
        # parents y protocols frame
        super(ProtocolFrame, self).__init__(screen, 20, screen.width, has_border=True, name="Protocol Submenu")
        self.model = model
        ip, parent, protocols,child_level = [(ip,parent,protocols,child_level) for ip,parent,protocols,child_level in self.model.cachered_ips if ip == self.model.selected_ip][0] or  ('','',[''],0)
        
        
        self.selection_item:int|None = None
        layout = Layout([1])
        self.add_layout(layout)
        self.title_label = Label(f"Protocolos para IP: {ip}")
        layout.add_widget(self.title_label)
        layout.add_widget(Divider())
        self.items = ListBox(
            height=6,
            options=[(protocol, i) for i, protocol in enumerate(protocols)],
            name="protocols",
            add_scroll_bar=True
        )
        layout.add_widget(self.items)
        layout.add_widget(Divider())
        layout.add_widget(Label("Presiona Q para regresar"))
        self.model.attach(self)
        self._update_protocols()
        
        #self.fix()
    def observerUpdate(self, **kwargs):
        """Método llamado automáticamente cuando el modelo cambia"""
        if 'selected_ip' in kwargs:
            self._update_protocols()
    def _update_protocols(self):
        """Actualizar la lista de protocolos basado en self.model.selected_ip"""
        selected_data = None
        for ip, parent, protocols, child_level in self.model.cachered_ips:
            if ip == self.model.selected_ip:
                selected_data = (ip, parent, protocols, child_level)
                break
        
        if not selected_data:
            self.title_label.text = f"Protocolos para IP: {self.model.selected_ip} (no encontrada)"
            self.items.options = []
            return
        
        ip, parent, protocols, child_level = selected_data
        self.title_label.text = f"Protocolos para IP: {ip} (nivel: {child_level})"
        self.items.options = [(protocol, i) for i, protocol in enumerate(protocols)]
        self.items.value = 0
        self.fix()
    def _on_select(self):
        # logica de si es una direccion ip o puerto
        ...
    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('E'),ord('e')]:
                #raise StopApplication(0)
                print([(ip,parent,protocols,child_level) for ip,parent,protocols,child_level in self.model.cachered_ips if ip == self.model.selected_ip][0])
                print(self.model.selected_ip,'*')
                raise ValueError("*")
            if event.key_code in [ord('Q'), ord('q')]:
                raise NextScene("main")
            if event.key_code == 10:
                # enter
                self.selection_item =  self.items.value
        return super(ProtocolFrame, self).process_event(event)