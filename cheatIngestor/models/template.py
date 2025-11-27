from json import dumps
class Template:
    desc:str
    linux:str
    windows:str
    noise_estimate:int
    def serialize(self):
        return dumps(vars())

class Technique:
    technique:str
    name:str
    templates:dict[str,Template]
    def serialize(self):
        return dumps(vars())