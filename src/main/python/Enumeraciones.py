from enum import Enum, auto

class TipoError(Enum):
    """Tipos de errores manejados por el compilador."""
    
    SINTACTICO = auto()
    SEMANTICO = auto()

    def __str__(self):
        return self.name

class CType(Enum):
    """Tipos de datos manejados por el compilador."""

    UNDETERMINED = ("undetermined", -1)
    VOID = ("void", 0)
    BOOL = ("bool", 1)
    CHAR = ("char", 2)
    INT = ("int", 3)
    FLOAT = ("float", 4)

    def __init__(self, text, rank):
        self.text = text
        self.rank = rank

    def __str__(self):
        return self.text
    
    def fromStr(texto: str):
        for t in CType:
            if t.text == texto:
                return t
        return CType.UNDETERMINED
