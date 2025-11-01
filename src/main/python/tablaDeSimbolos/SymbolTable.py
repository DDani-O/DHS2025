from Context import Contexto
from ID import ID
from Variable import Variable


class TS:
    _instance = None # Instancia única de la tabla de símbolos, según patrón singleton

    def __new__(cls): # Metodo creador
        if cls._instance is None: # Si no existe una instancia, crearla
            cls._instance = super(TS, cls).__new__(cls)
            # --- Inicialización ---
            cls._instance.contextos = [] # Pila de contextos para recorrido recursivo
            cls._instance.historialCTX = [] # Historial para guardar los contextos en orden de creación. Mantiene una referencia a cada contexto creado, incluso cuando se lo elimina de la pila
            cls._instance.addContexto() # Agregar el contexto global
        return cls._instance # Si existe una instancia, retornarla
    
    @staticmethod
    def getTS():
        """Método estático para obtener la instancia de la tabla de símbolos, según patrón singleton."""
        if TS._instance is None:
            TS._instance = TS()
        return TS._instance
    
    def addContexto(self):
        """Agrega un nuevo contexto (diccionario) a la pila de contextos y agrega una entrada al historial."""
        
        nuevo_contexto = Contexto()
        nuevo_contexto.nivel = len(self.contextos)

        self.contextos.append(nuevo_contexto)
        self.historialCTX.append(nuevo_contexto)

    def delContexto(self): 
        """Elimina el contexto actual (el último en la pila)."""
        if len(self.contextos) > 1: # No eliminar el contexto global
            self.contextos.pop()

    def addSimbolo(self, simbolo : ID):
        """Agrega un símbolo al contexto actual."""
        self.contextos[-1].addSimbolo(simbolo)

    def buscarSimbolo(self, nombre: str) -> ID:
        """Busca un símbolo recorriendo los contextos de manera recursiva, desde el actual hacia el global."""
        for contexto in reversed(self.contextos):
            simbolo = contexto.buscarSimbolo(nombre)
            if simbolo is not None:
                return simbolo
        return None  # Si no se encuentra el símbolo en ningún contexto
    
    def buscarSimboloContexto(self, nombre: str) -> ID:
        """Busca un símbolo SOLO en el contexto actual."""
        simbolo = self.contextos[-1].buscarSimbolo(nombre)
        return simbolo
    
    def imprimirTS(self):
        """Imprime la TS completa en un archivo, usando el historial de contextos para mantener la jerarquía de indentación y el orden en que se crean los contextos."""
        with open("ContenidoTS.txt", "w") as f:
            
            if not self.historialCTX:
                f.write("Tabla de símbolos vacía.\n")
                return

            for idx, contexto in enumerate(self.historialCTX):
                prefijo = '    ' * contexto.nivel
                f.write(f"{prefijo}--- Contexto #{idx} (nivel {contexto.nivel}) ---\n")

                simbolos = contexto.simbolos
                if not simbolos:
                    f.write(f"{prefijo}(vacío)\n")
                    continue # Salta al siguiente contexto

                # Cabecera de impresión
                f.write(f"{prefijo}{'Nombre':<20} {'Tipo':<12} {'Inicializado':<12} {'Usado':<6} Argumentos\n")

                # Impresión de los símbolos
                for nombre, simbolo in simbolos.items(): # 'items()' es un método estándar de diccionarios que devuelve una vista (parecido a un acceso directo) iterable de los pares (clave, valor)
                    # Obtener atributos básicos
                    tipo = simbolo.tipoDato
                    inicializado = simbolo.inicializado # En Py los valores booleanos se pueden castear a str directamente, así que no hace falta un if extra
                    usado = simbolo.usado

                    # Obtener los argumentos si se trata de una función
                    if isinstance(simbolo, Variable):
                        argumentos = "N/A"
                    else:
                        argumentos = ', '.join([arg.tipoDato for arg in simbolo.getListaArgs()]) if simbolo.getListaArgs() else "void" # Aplicamos condicional ternario para que el código quede más limpio nomás

                    # Imprimir los datos del símbolo
                    f.write(f"{prefijo}{nombre:<20} {str(tipo):<12} {str(inicializado):<12} {str(usado):<6} {argumentos}\n")
