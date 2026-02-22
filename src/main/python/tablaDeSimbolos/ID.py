from Enumeraciones import CType

class ID:
    def __init__(self, nombre: str, tipoDato: CType):
        self.nombre = nombre
        self.tipoDato = tipoDato
        self.inicializado = False
        self.usado = False

    def getNombre(self) -> str:
        return self.nombre

    def getTipoDato(self) -> CType:
        return self.tipoDato

    def getInicializado(self) -> bool:
        return self.inicializado

    def getUsado(self) -> bool:
        return self.usado

    def setInicializado(self):
        self.inicializado = True

    def setUsado(self):
        self.usado = True
