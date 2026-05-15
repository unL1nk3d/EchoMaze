from asciimatics.widgets import Frame, Layout, ListBox, Button, Label, TextBox, Text, PopUpDialog, Widget, Divider
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from tunnelsManager.models.implant import Implant

class ImplantsDashboardFrame(Frame):
    def __init__(self, screen: Screen, model):
        super(ImplantsDashboardFrame, self).__init__(
            screen,
            screen.height * 3 // 4,
            screen.width * 3 // 4,
            title="Implants Dashboard",
            can_scroll=True,
            reduce_cpu=True
        )
        self.model = model
        self.implants_usecase = model.implants_usecase

        self.implants_list = ListBox(
            height=10,
            options=[],
            name="implants_list",
            on_select=self._on_select
        )

        self.name_text = Text(label="Name:", name="implant_name")
        self.type_list = ListBox(
            height=5,
            options=[(t.capitalize(), t) for t in Implant.ALLOWED_TYPES],
            label="Type:",
            name="implant_type"
        )
        self.listener_ip_text = Text(label="LHOST:", name="lhost")
        self.listener_port_text = Text(label="LPORT:", name="lport")
        self.payload_text = TextBox(height=5, label="Payload:", name="payload", as_string=True)
        self.description_text = Text(label="Description:", name="description")

        self._rebuild_layout()
        self._refresh_data()

    def _rebuild_layout(self):
        self._layouts = []
        
        layout_list = Layout([100])
        self.add_layout(layout_list)
        layout_list.add_widget(self.implants_list)
        layout_list.add_widget(Divider())

        layout_form = Layout([50, 50])
        self.add_layout(layout_form)
        layout_form.add_widget(self.name_text, 0)
        layout_form.add_widget(self.type_list, 0)
        layout_form.add_widget(self.listener_ip_text, 1)
        layout_form.add_widget(self.listener_port_text, 1)
        layout_form.add_widget(self.description_text, 1)

        layout_payload = Layout([100])
        self.add_layout(layout_payload)
        layout_payload.add_widget(self.payload_text)

        layout_buttons = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout_buttons)
        layout_buttons.add_widget(Button("Generate", self._generate_payload), 0)
        layout_buttons.add_widget(Button("Save Implant", self._save_implant), 1)
        layout_buttons.add_widget(Button("Copy Payload", self._copy_payload), 2)
        layout_buttons.add_widget(Button("Delete", self._delete_implant), 3)
        layout_buttons.add_widget(Button("Close", self._close), 4)

        self.fix()

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('S'), ord('s')]:
                # Check if focused widget is LHOST or LPORT
                focused_widget = self.focussed_widget
                if focused_widget == self.listener_ip_text:
                    self._show_ip_selection(focused_widget)
                    return None
                elif focused_widget == self.listener_port_text:
                    self._show_port_selection(focused_widget, self.listener_ip_text.value)
                    return None
        return super(ImplantsDashboardFrame, self).process_event(event)

    def _show_ip_selection(self, target_widget):
        ips_with_data = self.model.cachered_ips
        if not ips_with_data:
            self._scene.add_effect(PopUpDialog(self._screen, "No IPs found in database", ["OK"]))
            return

        options = []
        for ip, _, protocols, _ in sorted(ips_with_data, key=lambda x: x[0]):
            services_str = f" [{', '.join(protocols[:3])}]" if protocols else ""
            display_text = f"{ip}{services_str}"
            options.append((display_text, ip))
        
        def _on_pick():
            target_widget.value = list_box.value
            self._scene.remove_effect(popup)

        layout = Layout([100], fill_frame=True)
        popup = Frame(self._screen, 10, 40, has_border=True, title="Select IP")
        popup.palette = self.palette
        popup.add_layout(layout)
        list_box = ListBox(Widget.FILL_FRAME, options, on_select=_on_pick)
        layout.add_widget(list_box)
        layout.add_widget(Button("Cancel", lambda: self._scene.remove_effect(popup)))
        popup.fix()
        self._scene.add_effect(popup)

    def _show_port_selection(self, target_widget, ip):
        if not ip:
            self._scene.add_effect(PopUpDialog(self._screen, "Please select/enter an LHOST first", ["OK"]))
            return

        repo = self.model.repo.repository
        all_ports = []
        if hasattr(repo, 'select_all_ports'):
            all_ports = repo.select_all_ports()
        
        ip_ports = [p for p in all_ports if p.ip == ip]
        if not ip_ports:
            self._scene.add_effect(PopUpDialog(self._screen, f"No ports found for {ip}", ["OK"]))
            return

        options = []
        for p in sorted(ip_ports, key=lambda x: x.port):
            options.append((f"{p.port} ({p.service_name})", str(p.port)))
        
        def _on_pick():
            target_widget.value = list_box.value
            self._scene.remove_effect(popup)

        layout = Layout([100], fill_frame=True)
        popup = Frame(self._screen, 10, 30, has_border=True, title=f"Ports for {ip}")
        popup.palette = self.palette
        popup.add_layout(layout)
        list_box = ListBox(Widget.FILL_FRAME, options, on_select=_on_pick)
        layout.add_widget(list_box)
        layout.add_widget(Button("Cancel", lambda: self._scene.remove_effect(popup)))
        popup.fix()
        self._scene.add_effect(popup)

    def _refresh_data(self):
        implants = self.implants_usecase.list_implants()
        options = []
        for i in implants:
            desc = f"ID:{i.id} | {i.name} ({i.implant_type}) - {i.created_at}"
            options.append((desc, i.id))
        self.implants_list.options = options

    def _generate_payload(self):
        self.save()
        i_type = self.data.get("implant_type")
        lhost = self.data.get("lhost")
        lport = self.data.get("lport")

        if not lhost or not lport or not lport.isdigit():
            self._scene.add_effect(PopUpDialog(self._screen, "LHOST and LPORT (digit) required", ["OK"]))
            return

        payload = self.implants_usecase.generate_payload(i_type, lhost, int(lport))
        self.payload_text.value = payload

    def _save_implant(self):
        self.save()
        data = self.data
        name = data.get("implant_name")
        i_type = data.get("implant_type")
        payload = data.get("payload")
        desc = data.get("description")

        if name and payload:
            self.implants_usecase.create_implant(name, i_type, payload, desc)
            self._refresh_data()
        else:
            self._scene.add_effect(PopUpDialog(self._screen, "Name and Payload required", ["OK"]))

    def _copy_payload(self):
        payload = self.payload_text.value
        if payload:
            self.model.copy_to_clipboard(payload)
            self._scene.add_effect(PopUpDialog(self._screen, "Payload copied to clipboard!", ["OK"]))

    def _delete_implant(self):
        selected_id = self.implants_list.value
        if selected_id is not None:
            self.implants_usecase.delete_implant(selected_id)
            self._refresh_data()

    def _on_select(self):
        selected_id = self.implants_list.value
        if selected_id is not None:
            implant = self.implants_usecase.get_implant(selected_id)
            if implant:
                self.name_text.value = implant.name
                self.type_list.value = implant.implant_type
                self.payload_text.value = implant.payload
                self.description_text.value = implant.description

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene("main")
