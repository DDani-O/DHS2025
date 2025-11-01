from ID import ID

class Contexto:
    def __init__(self):
        self.simbolos = {}  # Diccionario para almacenar los símbolos en este contexto
        self.nivel = 0 # Nivel de anidamiento del contexto (para impresión)

    def addSimbolo(self, simbolo: ID):
        """Agrega un símbolo al contexto actual."""
        nombre = simbolo.getNombre()
        if self.buscarSimbolo(nombre) is None:  # Verifica si el símbolo ya existe
            self.simbolos[nombre] = simbolo
        else:
            print(f"El símbolo '{nombre}' ya existe en el contexto actual.")
            # Acá podríamos lanzar una excepción

    def buscarSimbolo(self, nombre: str) -> ID:
        """Busca un símbolo en el contexto actual."""
        for identificador in self.simbolos:
            if identificador == nombre:
                return self.simbolos[identificador]
        return None  # Si no se encuentra el símbolo
        