from UI.frames.admin_dashboard import AdminDashboardFrame
from UI.frames.artifacts_frame import ArtifactsFrame
from UI.frames.IPframe import IPFrame
from UI.frames.searchFrame import SearchFrame
from UI.frames.ProtocolFrame import ProtocolFrame
from UI.frames.tree_ip_frame import TreeIPFrame
from UI.frames.SuggestionsFrame import SuggestionsFrame
from UI.frames.TerminalFrame import TerminalFrame
from UI.frames.tunnels_frame import TunnelsDashboardFrame
from UI.frames.implants_frame import ImplantsDashboardFrame
from UI.frames.agent_frame import AgentDashboardFrame
from UI.models import UIMapper,GenericModel,RepositoryModel
from UI.opsec_panel import OpSecPanel
from asciimatics.scene import Scene
from asciimatics.screen import Screen




def demo(screen,model):
    opsec = OpSecPanel(screen, model)
    # Wire OpSecPanel as observer of GenericModel
    model.attach(opsec)

    tree_frame = TreeIPFrame(screen, model)
    # Wire TreeIPFrame as observer for inline suggestions & risk colors
    model.attach(tree_frame)

    scenes = [
        
        Scene([tree_frame], -1, name="main"),
        #Scene([SuggestionsFrame(screen,model)],-1,name='suggestions'),
        # si suggestion se agrega como un popup no puede estar registrado como scene
        # o se crashea la app
        Scene([TerminalFrame(screen,model)],-1,name='terminal'),
        # Scene([IPFrame(screen,model)], -1, name="main"),
        Scene([SearchFrame(screen,model)], -1,name="search"),
        Scene([ProtocolFrame(screen,model)], -1, name="protocols"),  # ip_index se actualiza dinámicamente
        Scene([opsec], -1, name="opsec"),
        Scene([AdminDashboardFrame(screen, model)], -1, name="admin"),
        Scene([ArtifactsFrame(screen, model)], -1, name="artifacts"),
        Scene([TunnelsDashboardFrame(screen, model)], -1, name="tunnels"),
        Scene([ImplantsDashboardFrame(screen, model)], -1, name="implants"),
        Scene([AgentDashboardFrame(screen, model)], -1, name="agent")
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scenes[0])

def run_ui(model:GenericModel):
     try:
        Screen.wrapper(func=demo,arguments=(model,))
     except KeyboardInterrupt:
        exit(0)
