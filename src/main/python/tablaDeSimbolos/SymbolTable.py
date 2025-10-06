class TS:
    _instance = None # Instancia única de la tabla de símbolos

    def __new__(cls): # Metodo creador
        if cls._instance is None: # Si no existe una instancia, crearla
            cls._instance = super(TS, cls).__new__(cls)
            cls._instance.contextos = [] # Inicialización
            cls._instance.addContexto() # Agregar el contexto global
        return cls._instance # Si existe una instancia, retornarla
    
    @staticmethod
    def getTS(): # Método estático para obtener la instancia de la tabla de símbolos
        if TS._instance is None:
            TS._instance = TS()
        return TS._instance
    
    def addContexto(self): # Agrega un nuevo contexto (diccionario) a la pila de contextos
        nuevo_contexto = Contexto()
        self.contextos.append(nuevo_contexto)
        return nuevo_contexto # Retorna por si lo queres usar directamente

    def delContexto(self): # Elimina el contexto actual (el último en la pila)
        if len(self.contextos) > 1: # No eliminar el contexto global
            self.contextos.pop()

    def addSimbolo(self, nombre, valor): # Agrega un símbolo al contexto actual
        self.contextos[-1].addSimbolo(nombre, valor)

    def buscarSimbolo(self, nombre): # Busca un símbolo en los contextos desde el actual hacia el global
        for contexto in reversed(self.contextos):
            valor = contexto.buscarSimbolo(nombre)
            if valor is not None:
                return valor
        return None # Si no se encuentra el símbolo