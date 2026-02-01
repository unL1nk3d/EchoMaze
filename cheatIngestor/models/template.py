from json import dumps
class Template:
    def __init__(self, desc, linux, windows, noise_estimate):
        self.desc = desc
        self.linux = linux
        self.windows = windows
        self.noise_estimate = noise_estimate
        self.generic = False
    def serialize(self):
        return dumps(vars())
    def set_generic_flag(self):
        self.generic = True

class Technique:
    def __init__(self, technique, name, templates):
        self.technique = technique
        self.name = name
        self.templates = templates
    def serialize(self):
        return dumps(vars())
    def is_void(self):
        if all([self.technique,self.name,self.templates]):
            return True
        return False