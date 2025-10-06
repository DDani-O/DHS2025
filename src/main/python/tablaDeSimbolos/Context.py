from ID import ID

class Contexto:
    def __init__(self):
        self.simbolos = {}  # Diccionario para almacenar los símbolos en este contexto

    def addSimbolo(self, simbolo: ID):
        nombre = simbolo.getNombre()
        if self.buscarSimbolo(nombre) is None:  # Verifica si el símbolo ya existe
            self.simbolos[nombre] = simbolo
        else:
            print(f"El símbolo '{nombre}' ya existe en el contexto actual.")
            # Acá podríamos lanzar una excepción

    def buscarSimbolo(self, nombre: str) -> ID:
        for simbolo in self.simbolos:
            if simbolo == nombre:
                return self.simbolos[simbolo]
        return None  # Si no se encuentra el símbolo
        