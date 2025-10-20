from typing import List
from ID import ID

class Funcion(ID) :
    # args = [] # Esto está mal acá porque se define como una variable de clase pero lo que necesitamos es una var de instancia

    def __init__(self):
        super().__init__()
        self.args: List[ID] = []

    def getListaArgs(self) -> List[ID]:
        return self.args