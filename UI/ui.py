from UI.frames.IPframe import IPFrame
from UI.frames.searchFrame import SearchFrame
from UI.frames.ProtocolFrame import ProtocolFrame
from UI.frames.tree_ip_frame import TreeIPFrame
from UI.frames.SuggestionsFrame import SuggestionsFrame
from UI.frames.TerminalFrame import TerminalFrame
from UI.models import UIMapper,GenericModel,RepositoryModel
from asciimatics.scene import Scene
from asciimatics.screen import Screen




def demo(screen,model):
    scenes = [
        
        Scene([TreeIPFrame(screen,model)], -1, name="main"),
        # Scene([SuggestionsFrame(screen,model)],-1,name='suggestions'),
        # si suggestion se agrega como un popup no puede estar registrado como scene
        # o se crashea la app
        Scene([TerminalFrame(screen,model)],-1,name='terminal'),
        # Scene([IPFrame(screen,model)], -1, name="main"),
        Scene([SearchFrame(screen,model)], -1,name="search"),
        Scene([ProtocolFrame(screen,model)], -1, name="protocols")  # ip_index se actualiza dinámicamente
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scenes[0])

def run_ui(model:GenericModel):
     try:
        Screen.wrapper(func=demo,arguments=(model,))
     except KeyboardInterrupt:
        exit(0)
