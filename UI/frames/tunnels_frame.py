from asciimatics.widgets import Frame, Layout, ListBox, Button, Label, TextBox, Text, PopUpDialog, Widget
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from tunnelsManager.core import TunnelsUseCase
from tunnelsManager.models.tunnel import Tunnel

class TunnelsDashboardFrame(Frame):
    def __init__(self, screen: Screen, model):
        super(TunnelsDashboardFrame, self).__init__(
            screen,
            screen.height * 3 // 4,
            screen.width * 3 // 4,
            title="Tunnels Dashboard",
            can_scroll=True,
            reduce_cpu=True
        )
        self.model = model
        self.tunnels_usecase = model.tunnels
        self._options_visible = False

        self.stats_label = Label("")
        self.tunnels_list = ListBox(
            height=8,
            options=[],
            name="tunnels_list",
            on_select=self._on_select
        )

        self.source_ip_text = Text(label="Source IP:", name="source_ip")
        self.local_port_text = Text(label="Local Port:", name="local_port")
        self.dest_ip_text = Text(label="Dest IP (opt):", name="dest_ip")
        self.remote_port_text = Text(label="Remote Port (opt):", name="remote_port")
        self.check_interval_text = Text(label="Check Interval (s):", name="check_interval")
        self.technique_list = ListBox(
            height=3,
            options=[("None", Tunnel.TECHNIQUE_NONE), ("Beaconing", Tunnel.TECHNIQUE_BEACONING)],
            label="Technique:",
            name="technique"
        )
        self.type_list = ListBox(
            height=4,
            options=[(t, t) for t in Tunnel.ALLOWED_TYPES],
            label="Type:",
            name="tunnel_type"
        )

        self._rebuild_layout()
        self._refresh_data()

    def _rebuild_layout(self):
        # Clear existing layouts
        self._layouts = []

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

        if self._options_visible:
            layout_options_title = Layout([100])
            self.add_layout(layout_options_title)
            layout_options_title.add_widget(Label("--- ADVANCED OPTIONS (O to hide) ---"))

            layout_policy = Layout([33, 33, 33])
            self.add_layout(layout_policy)
            layout_policy.add_widget(self.check_interval_text, 0)
            layout_policy.add_widget(self.technique_list, 1)
            layout_policy.add_widget(self.type_list, 2)

            layout_adv_buttons = Layout([1, 1, 1, 1, 1, 1])
            self.add_layout(layout_adv_buttons)
            layout_adv_buttons.add_widget(Button("Set Policy", self._set_policy), 0)
            layout_adv_buttons.add_widget(Button("Set Tech", self._set_technique), 1)
            layout_adv_buttons.add_widget(Button("Eval Ent", self._evaluate_entropy), 2)
            layout_adv_buttons.add_widget(Button("Sim Transf", self._simulate_transfer), 3)
            layout_adv_buttons.add_widget(Button("Activating", self._set_activating), 4)
            layout_adv_buttons.add_widget(Button("Send Beacon", self._send_beacon), 5)

        layout_buttons = Layout([1, 1, 1, 1, 1, 1, 1])
        self.add_layout(layout_buttons)
        layout_buttons.add_widget(Button("Add Tunnel", self._add_tunnel), 0)
        layout_buttons.add_widget(Button("Next Phase", self._advance_phase), 1)
        layout_buttons.add_widget(Button("Activate", self._activate_tunnel), 2)
        layout_buttons.add_widget(Button("Deactivate", self._deactivate_tunnel), 3)
        layout_buttons.add_widget(Button("Delete", self._delete_tunnel), 4)
        layout_buttons.add_widget(Button("Options (O)", self._toggle_options), 5)
        layout_buttons.add_widget(Button("Close", self._close), 6)

        self.fix()

    def _toggle_options(self):
        self._options_visible = not self._options_visible
        self._rebuild_layout()

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('O'), ord('o')]:
                self._toggle_options()
                return None
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
        global_e = stats.get('global_entropy', 0.0)
        global_w = stats.get('entropy_warning', "")
        self.stats_label.text = f"Stats - Tot:{stats['total']} | Act:{stats['active']} | Ent:{global_e:.2f} ({global_w})"
        self.check_interval_text.value = str(self.tunnels_usecase.check_interval)

        tunnels = self.tunnels_usecase.get_all_tunnels()
        options = []
        for t in tunnels:
            hanging_str = "[HANGING] " if t.is_hanging else ""
            remote_str = f"-> {t.dest_ip}:{t.remote_port}" if t.dest_ip else ""
            tech_str = f" [{t.technique}]" if t.technique != Tunnel.TECHNIQUE_NONE else ""
            type_str = f" <{t.tunnel_type}>"
            desc = f"{hanging_str}ID:{t.id} | {t.source_ip}:{t.local_port} {remote_str} {type_str} ({t.status}) [{t.phase}]{tech_str}"
            options.append((desc, t.id))

        self.tunnels_list.options = options

    def _evaluate_entropy(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.evaluate_tunnel_entropy(selected_id)
            self._refresh_data()
            
            # Show evaluation in a PopUpDialog to keep the dashboard clean
            tunnels = self.tunnels_usecase.get_all_tunnels()
            for t in tunnels:
                if t.id == selected_id:
                    msg = (f"Entropy Evaluation for Tunnel {t.id}:\n\n"
                           f"Type: {t.tunnel_type}\n"
                           f"Carrier Data Type: {t.data_type}\n"
                           f"Entropy Score: {t.entropy_score:.2f}\n"
                           f"Assessment: {t.entropy_warning}")
                    self._scene.add_effect(PopUpDialog(self._screen, msg, ["OK"]))
                    break

    def _simulate_transfer(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            # Simulate 1KB transfer for audit visibility
            self.tunnels_usecase.register_data_transfer(selected_id, 1024, 512)
            self._refresh_data()

    def _advance_phase(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.advance_tunnel_phase(selected_id)
            self._refresh_data()

    def _set_policy(self):
        self.save()
        val = self.data.get("check_interval")
        if val and val.isdigit():
            self.tunnels_usecase.set_connection_check_policy(int(val))
            self._scene.add_effect(PopUpDialog(self._screen, f"Policy updated: {val}s", ["OK"]))
            self._refresh_data()

    def _set_technique(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.save()
            tech = self.data.get("technique")
            self.tunnels_usecase.set_tunnel_technique(selected_id, tech)
            self._refresh_data()

    def _activate_tunnel(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.activate_tunnel(selected_id)
            self._refresh_data()

    def _set_activating(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.set_activating_status(selected_id)
            self._refresh_data()

    def _deactivate_tunnel(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.deactivate_tunnel(selected_id)
            self._refresh_data()

    def _send_beacon(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            success = self.tunnels_usecase.process_implant_beacon(selected_id)
            msg = "Beacon received and processed!" if success else "Beacon ignored (Deactivated, Tech None, or invalid ID)"
            self._scene.add_effect(PopUpDialog(self._screen, msg, ["OK"]))
            self._refresh_data()

    def _add_tunnel(self):
        self.save()
        data = self.data
        src_ip = data.get("source_ip")
        local_p = data.get("local_port")
        dest_ip = data.get("dest_ip")
        remote_p = data.get("remote_port")
        t_type = data.get("tunnel_type")

        if src_ip and local_p and local_p.isdigit():
            lp = int(local_p)
            rp = int(remote_p) if remote_p and remote_p.isdigit() else None
            self.tunnels_usecase.create_tunnel(src_ip, lp, dest_ip, rp, tunnel_type=t_type)
            # Clear fields after successful addition
            self.source_ip_text.value = ""
            self.local_port_text.value = ""
            self._refresh_data()

    def _delete_tunnel(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            self.tunnels_usecase.delete_tunnel(selected_id)
            self._refresh_data()

    def _on_select(self):
        selected_id = self.tunnels_list.value
        if selected_id is not None:
            tunnels = self.tunnels_usecase.get_all_tunnels()
            for t in tunnels:
                if t.id == selected_id:
                    self.technique_list.value = t.technique
                    self.type_list.value = t.tunnel_type
                    break

    def _close(self):
        self._scene.remove_effect(self)
        raise NextScene("main")
