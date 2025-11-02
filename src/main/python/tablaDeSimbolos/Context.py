from ID import ID

class Contexto:
    def __init__(self):
        self.simbolos = {}  # Diccionario para almacenar los símbolos en este contexto
        self.nivel = 0 # Nivel de anidamiento del contexto (para impresión)
        self.declaraciones_permitidas = True # Control para permitir solo declaraciones al comienzo del contexto

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

    def canDeclarar(self) -> bool:
        """Devuelve True si aún se permiten declaraciones en este contexto."""
        return self.declaraciones_permitidas

    def forbidDeclaraciones(self):
        """Marca que a partir de ahora no se permiten más declaraciones en este contexto."""
        self.declaraciones_permitidas = False
