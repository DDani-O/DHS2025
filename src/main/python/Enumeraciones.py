from enum import Enum, auto

class TipoError(Enum):
    """Enumeración para los tipos de errores del compilador."""
    
    SINTACTICO = auto()
    SEMANTICO = auto()

    def __str__(self): # Sobreescribimos para que imprima solo el nombre
        return self.name
