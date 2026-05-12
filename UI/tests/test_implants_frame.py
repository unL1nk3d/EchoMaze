import unittest
from unittest.mock import MagicMock, patch
from asciimatics.screen import Screen
from asciimatics.event import KeyboardEvent
from UI.frames.implants_frame import ImplantsDashboardFrame

class TestImplantsDashboardFrame(unittest.TestCase):
    def setUp(self):
        self.screen = MagicMock(spec=Screen)
        self.screen.width = 80
        self.screen.height = 24
        self.screen.colours = 8
        self.screen.unicode_aware = True
        
        self.model = MagicMock()
        self.implants_usecase = MagicMock()
        self.model.implants = self.implants_usecase
        
        # Sample IPs for selection testing
        self.model.cachered_ips = [
            ('192.168.1.1', '', [], 0)
        ]
        
        self.implants_usecase.list_implants.return_value = []

        with patch('asciimatics.widgets.Frame.fix'):
             self.frame = ImplantsDashboardFrame(self.screen, self.model)
             self.frame._scene = MagicMock()

    def test_process_event_s_key_ip(self):
        """Verify that pressing 's' triggers IP selection when focused on LHOST."""
        event = KeyboardEvent(ord('s'))
        
        with patch('UI.frames.implants_frame.ImplantsDashboardFrame.focussed_widget', new_callable=unittest.mock.PropertyMock) as mock_focus:
            mock_focus.return_value = self.frame.listener_ip_text
            
            with patch.object(self.frame, '_show_ip_selection') as mock_show:
                self.frame.process_event(event)
                mock_show.assert_called_once_with(self.frame.listener_ip_text)

    def test_process_event_s_key_port(self):
        """Verify that pressing 's' triggers port selection when focused on LPORT."""
        event = KeyboardEvent(ord('s'))
        self.frame.listener_ip_text.value = "192.168.1.1"
        
        with patch('UI.frames.implants_frame.ImplantsDashboardFrame.focussed_widget', new_callable=unittest.mock.PropertyMock) as mock_focus:
            mock_focus.return_value = self.frame.listener_port_text
            
            with patch.object(self.frame, '_show_port_selection') as mock_show:
                self.frame.process_event(event)
                mock_show.assert_called_once_with(self.frame.listener_port_text, "192.168.1.1")

if __name__ == '__main__':
    unittest.main()
