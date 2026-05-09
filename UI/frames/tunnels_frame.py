from asciimatics.widgets import Frame, Layout, ListBox, Button, Label, TextBox, Text, PopUpDialog, Widget
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from tunnelsManager.core import TunnelsUseCase

class TunnelsDashboardFrame(Frame):
    def __init__(self, screen: Screen, model):
        super(TunnelsDashboardFrame, self).__init__(
            screen,
            screen.height * 3 // 4,
            screen.width * 3 // 4,
            title="Tunnels Dashboard",
            can_scroll=False,
            reduce_cpu=True
        )
        self.model = model
        self.tunnels_usecase = model.tunnels

        self.stats_label = Label("")
        self.tunnels_list = ListBox(
            height=10,
            options=[],
            name="tunnels_list",
            on_select=self._on_select
        )

        self.source_ip_text = Text(label="Source IP:", name="source_ip")
        self.local_port_text = Text(label="Local Port:", name="local_port")
        self.dest_ip_text = Text(label="Dest IP (opt):", name="dest_ip")
        self.remote_port_text = Text(label="Remote Port (opt):", name="remote_port")

        layout_stats = Layout([100])
        self.add_layout(layout_stats)
        layout_stats.add_widget(self.stats_label)

        layout_list = Layout([100])
        self.add_layout(layout_list)
        layout_list.add_widget(self.tunnels_list)

        layout_form = Layout([50, 50])
        self.add_layout(layout_form)
        layout_form.add_widget(self.source_ip_text, 0)
        layout_form.add_widget(self.local_port_text, 0)
        layout_form.add_widget(self.dest_ip_text, 1)
        layout_form.add_widget(self.remote_port_text, 1)

        layout_buttons = Layout([1, 1, 1])
        self.add_layout(layout_buttons)
        layout_buttons.add_widget(Button("Add Tunnel", self._add_tunnel), 0)
        layout_buttons.add_widget(Button("Delete Selected", self._delete_tunnel), 1)
        layout_buttons.add_widget(Button("Close", self._close), 2)

        self.fix()
        self._refresh_data()

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('S'), ord('s')]:
                # Check if focused widget is one of the IP or Port fields
                focused_widget = self.focussed_widget
                if focused_widget in [self.source_ip_text, self.dest_ip_text]:
                    self._show_ip_selection(focused_widget)
                    return None
                elif focused_widget in [self.local_port_text, self.remote_port_text]:
                    # Determine which IP field corresponds to this port field
                    ip_widget = self.source_ip_text if focused_widget == self.local_port_text else self.dest_ip_text
                    self._show_port_selection(focused_widget, ip_widget.value)
                    return None
        return super(TunnelsDashboardFrame, self).process_event(event)

    def _show_ip_selection(self, target_widget):
        # Use cachered_ips which contains (ip, parent, protocols, level)
        ips_with_data = self.model.cachered_ips
        
        if not ips_with_data:
            self._scene.add_effect(PopUpDialog(self._screen, "No IPs found in database", ["OK"]))
            return

        # Sort and format options: "IP [services]"
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
            self._scene.add_effect(PopUpDialog(self._screen, "Please select/enter an IP first", ["OK"]))
            return

        # Fetch ports from repository via model
        repo = self.model.repo.repository
        all_ports = []
        if hasattr(repo, 'select_all_ports'):
            all_ports = repo.select_all_ports()
        
        # Filter ports by IP
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
        stats = self.tunnels_usecase.get_tunnel_stats()
        self.stats_label.text = f"Stats - Total: {stats['total']} | Active: {stats['active']} | Hanging (Warning): {stats['hanging']}"

        tunnels = self.tunnels_usecase.get_all_tunnels()
        options = []
        for t in tunnels:
            hanging_str = "[HANGING] " if t.is_hanging else ""
            remote_str = f"-> {t.dest_ip}:{t.remote_port}" if t.dest_ip else ""
            desc = f"{hanging_str}ID:{t.id} | {t.source_ip}:{t.local_port} {remote_str} ({t.status})"
            options.append((desc, t.id))

        self.tunnels_list.options = options

    def _add_tunnel(self):
        self.save()
        data = self.data
        src_ip = data.get("source_ip")
        local_p = data.get("local_port")
        dest_ip = data.get("dest_ip")
        remote_p = data.get("remote_port")

        if src_ip and local_p and local_p.isdigit():
            lp = int(local_p)
            rp = int(remote_p) if remote_p and remote_p.isdigit() else None
            self.tunnels_usecase.create_tunnel(src_ip, lp, dest_ip, rp)
            self._refresh_data()

    def _delete_tunnel(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.delete_tunnel(selected_id)
            self._refresh_data()

    def _on_select(self):
        pass

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene("main")
