from typing import List
from tablaDeSimbolos.ID import ID
from Enumeraciones import CType

class Funcion(ID):
    def __init__(self, nombre: str, tipoDato: str, args: List[CType] = None):
        super().__init__(nombre, tipoDato) # ID espera (nombre, tipoDato)
        self.args: List[CType] = args if args is not None else []

    def getListaArgs(self) -> List[CType]:
        return self.args