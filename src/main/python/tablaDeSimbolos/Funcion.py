from typing import List, Optional
from tablaDeSimbolos.ID import ID
from tablaDeSimbolos.Variable import Variable

class Funcion(ID):
    def __init__(self, nombre: str, tipoDato: str, args: Optional[List[Variable]] = None):
        super().__init__(nombre, tipoDato) # ID espera (nombre, tipoDato)
        self.args: List[Variable] = args if args is not None else []

    def getListaArgs(self) -> List[Variable]:
        return self.args