from typing import List, Optional
from ID import ID
from Variable import Variable

class Funcion(ID):
    """Representa una función en la tabla de símbolos.

    Atributos:
    - nombre, tipoDato (heredados de ID)
    - args: lista de objetos Variable que representan los parámetros (pueden tener nombre vacío si es un prototipo)
    - (inicializado, usado) están definidos en la clase base ID y representan si es definición/prototipo y si fue llamada.
    """

    def __init__(self, nombre: str, tipoDato: str, args: Optional[List[Variable]] = None, inicializado: bool = False):
        # ID espera (nombre, tipoDato)
        super().__init__(nombre, tipoDato)
        self.args: List[Variable] = args if args is not None else []
        # `inicializado` y `usado` ya existen en la clase base ID; ajustamos si el constructor pide inicializado=True
        if inicializado:
            self.setInicializado()

    def getListaArgs(self) -> List[Variable]:
        return self.args