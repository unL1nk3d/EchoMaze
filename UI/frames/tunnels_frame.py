from asciimatics.widgets import Frame, Layout, ListBox, Button, Label, TextBox, Text
from asciimatics.exceptions import NextScene
from asciimatics.screen import Screen
from tunnelsManager.core import TunnelsUseCase

class TunnelsDashboardFrame(Frame):
    def __init__(self, screen: Screen, tunnels_usecase: TunnelsUseCase):
        super(TunnelsDashboardFrame, self).__init__(
            screen,
            screen.height * 3 // 4,
            screen.width * 3 // 4,
            title="Tunnels Dashboard",
            can_scroll=False,
            reduce_cpu=True
        )
        self.tunnels_usecase = tunnels_usecase

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
