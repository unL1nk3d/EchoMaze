import unittest
from unittest.mock import MagicMock, patch
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from UI.frames.tunnels_frame import TunnelsDashboardFrame

class TestTunnelsDashboardFrame(unittest.TestCase):
    def setUp(self):
        self.screen = MagicMock(spec=Screen)
        self.screen.width = 80
        self.screen.height = 24
        self.screen.colours = 8
        self.screen.unicode_aware = True
        
        self.model = MagicMock()
        self.tunnels_usecase = MagicMock()
        self.tunnels_usecase.check_interval = 60
        self.model.tunnels = self.tunnels_usecase
        
        # Sample IPs for selection testing
        self.model.cachered_ips = [
            ('192.168.1.1', '', [], 0),
            ('10.0.0.1', '', [], 0)
        ]
        
        # Sample tunnels for list testing
        self.tunnel1 = MagicMock(
            id=1, source_ip='192.168.1.1', local_port=8080, 
            dest_ip='10.0.0.1', remote_port=80, status='active', 
            is_hanging=False, entropy_score=0.0, entropy_warning='Pending',
            data_sent_bytes=0, data_received_bytes=0, phase='tunnel creation',
            tunnel_type='HTTP', technique='none'
        )
        self.tunnels_usecase.get_all_tunnels.return_value = [self.tunnel1]
        self.tunnels_usecase.get_tunnel_stats.return_value = {
            'total': 1, 'active': 1, 'hanging': 0, 
            'disconnected': 0, 'deactivated': 0, 
            'activating': 0, 'filtered': 0,
            'global_entropy': 0.0, 'entropy_warning': 'Low'
        }

        # Global patch for Frame.fix to avoid layout calculation issues with mocks
        with patch('asciimatics.widgets.Frame.fix'):
             self.frame = TunnelsDashboardFrame(self.screen, self.model)
             self.frame._scene = MagicMock()

    def test_initialization(self):
        """Verify that the frame initializes with correct widgets and data."""
        # asciimatics adds spaces to the title
        self.assertEqual(self.frame.title.strip(), "Tunnels Dashboard")
        self.assertEqual(len(self.frame.tunnels_list.options), 1)
        self.assertIn("192.168.1.1:8080", self.frame.tunnels_list.options[0][0])

    def test_refresh_data(self):
        """Verify that _refresh_data updates stats and tunnel list."""
        self.tunnel2 = MagicMock(
            id=2, source_ip='192.168.1.2', local_port=9090, 
            dest_ip=None, remote_port=None, status='disconnected', 
            is_hanging=True, entropy_score=1.5, entropy_warning='OK',
            data_sent_bytes=100, data_received_bytes=50, phase='tunnel creation',
            tunnel_type='DNS', technique='none'
        )
        self.tunnels_usecase.get_all_tunnels.return_value = [self.tunnel1, self.tunnel2]
        self.tunnels_usecase.get_tunnel_stats.return_value = {
            'total': 2, 'active': 1, 'hanging': 1, 
            'disconnected': 1, 'deactivated': 0, 
            'activating': 0, 'filtered': 0,
            'global_entropy': 1.2, 'entropy_warning': 'Low'
        }
        
        self.frame._refresh_data()
        
        self.assertEqual(len(self.frame.tunnels_list.options), 2)
        self.assertIn("[HANGING]", self.frame.tunnels_list.options[1][0])
        self.assertIn("Stats - Tot:2", self.frame.stats_label.text)
        self.assertIn("Act:1", self.frame.stats_label.text)
        self.assertIn("Ent:1.20", self.frame.stats_label.text)

    def test_add_tunnel(self):
        """Verify that _add_tunnel calls the use case with correct data."""
        self.frame._toggle_options() # Show options so fields are added to layout and saved
        self.frame.source_ip_text.value = "172.16.0.1"
        self.frame.local_port_text.value = "4444"
        self.frame.dest_ip_text.value = "10.10.10.10"
        self.frame.remote_port_text.value = "443"
        self.frame.type_list.value = "DNS"
        
        self.frame._add_tunnel()
        
        self.tunnels_usecase.create_tunnel.assert_called_with("172.16.0.1", 4444, "10.10.10.10", 443, tunnel_type="DNS")
        self.tunnels_usecase.get_all_tunnels.assert_called()

    def test_delete_tunnel(self):
        """Verify that _delete_tunnel calls the use case with the selected ID."""
        self.frame.tunnels_list.value = 1
        self.frame._delete_tunnel()
        
        self.tunnels_usecase.delete_tunnel.assert_called_with(1)
        self.tunnels_usecase.get_all_tunnels.assert_called()

    def test_set_policy(self):
        """Verify that _set_policy updates the use case check interval."""
        self.frame._toggle_options() # Show options
        def mock_set_policy(val):
            self.tunnels_usecase.check_interval = val
        self.tunnels_usecase.set_connection_check_policy.side_effect = mock_set_policy

        self.frame.check_interval_text.value = "45"
        self.frame._set_policy()
        
        self.tunnels_usecase.set_connection_check_policy.assert_called_with(45)
        self.assertEqual(self.frame.check_interval_text.value, "45")

    def test_activate_deactivate_buttons(self):
        """Verify that activate/deactivate buttons call the use case."""
        self.frame.tunnels_list.value = 1
        
        self.frame._activate_tunnel()
        self.tunnels_usecase.activate_tunnel.assert_called_with(1)
        
        self.frame._toggle_options() # Activating is now an advanced option
        self.frame._set_activating()
        self.tunnels_usecase.set_activating_status.assert_called_with(1)
        
        self.frame._deactivate_tunnel()
        self.tunnels_usecase.deactivate_tunnel.assert_called_with(1)

    def test_technique_and_beacon_buttons(self):
        """Verify tech selection and beacon trigger call the use case."""
        self.frame._toggle_options() # Show options
        self.frame.tunnels_list.value = 1
        self.frame.technique_list.value = "beaconing"
        
        self.frame._set_technique()
        self.tunnels_usecase.set_tunnel_technique.assert_called_with(1, "beaconing")
        
        self.frame._send_beacon()
        self.tunnels_usecase.process_implant_beacon.assert_called_with(1)

    def test_process_event_s_key(self):
        """Verify that pressing 's' triggers IP selection when focused on an IP field."""
        event = KeyboardEvent(ord('s'))
        
        # Use PropertyMock because focussed_widget is a read-only property
        with patch('UI.frames.tunnels_frame.TunnelsDashboardFrame.focussed_widget', new_callable=unittest.mock.PropertyMock) as mock_focus:
            mock_focus.return_value = self.frame.source_ip_text
            
            with patch.object(self.frame, '_show_ip_selection') as mock_show:
                self.frame.process_event(event)
                mock_show.assert_called_once_with(self.frame.source_ip_text)

    def test_process_event_s_key_port(self):
        """Verify that pressing 's' triggers port selection when focused on a port field."""
        event = KeyboardEvent(ord('s'))
        self.frame.source_ip_text.value = "192.168.1.1"
        
        with patch('UI.frames.tunnels_frame.TunnelsDashboardFrame.focussed_widget', new_callable=unittest.mock.PropertyMock) as mock_focus:
            mock_focus.return_value = self.frame.local_port_text
            
            with patch.object(self.frame, '_show_port_selection') as mock_show:
                self.frame.process_event(event)
                mock_show.assert_called_once_with(self.frame.local_port_text, "192.168.1.1")

    @patch('asciimatics.widgets.Frame.fix')
    def test_show_ip_selection(self, mock_fix):
        """Verify that _show_ip_selection displays a popup with unique IPs and services."""
        # Add a duplicate IP with different service
        self.model.cachered_ips = [
            ('192.168.1.1', '', ['http'], 0),
            ('10.0.0.1', '', ['ssh'], 0)
        ]
        
        with patch('UI.frames.tunnels_frame.ListBox') as mock_listbox:
            self.frame._show_ip_selection(self.frame.source_ip_text)
            
            # Check if ListBox was created with unique IPs and services
            args, kwargs = mock_listbox.call_args
            options = args[1]
            self.assertEqual(len(options), 2)
            self.assertIn("192.168.1.1 [http]", options[1][0])
            self.assertIn("10.0.0.1 [ssh]", options[0][0])

if __name__ == '__main__':
    unittest.main()
