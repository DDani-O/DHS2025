from compiladorParser import compiladorParser
from compiladorListener import compiladorListener
from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Variable import Variable
from Enumeraciones import TipoError

class Escucha(compiladorListener) :
    # Esta clase personalizada la creamos porque el Listener original se sobreescribe cada vez que se vuelve a generar el parser.
    # Con esto podemos definir los metodos que nos interesen y que permanezcan.
    
    def __init__(self):
        super().__init__()
        self.TS = TS.getTS()
        self.huboErrores = False

    # ------------------------------
    # ---------- Utilidad ----------
    # ------------------------------

    def registrarError(self, tipo : TipoError, msj : str):
        self.huboErrores = True
        print(f"ERROR {tipo}: {msj}")

    # ----------------------------
    # ---------- Inicio ----------
    # ----------------------------

    def enterPrograma(self, ctx:compiladorParser.ProgramaContext):
        with open("ContenidoTS.txt", "w") as f:
            pass  # Limpiamos el archivo viejo
        print(" ------ Comienza el parsing ------ ")

    def exitPrograma(self, ctx:compiladorParser.ProgramaContext):
        if self.huboErrores:
            with open("ContenidoTS.txt", "w") as f:
                f.write("Imposible generar la TS: Se encontraron errores durante el parsing.\n")
        else:
            # Imprimir la TS completa al finalizar el parsing
            self.TS.imprimirTS()
        print(" ------ Termina el parsing ------ ")

    # -----------------------------------------
    # ---------- Manejo de contextos ----------
    # -----------------------------------------
    # En C, la creación de contextos no se limita únicamente a contextos en bloques con llave, sino que también se crean contextos en estructuras de control.
    # Esto implica que también tendríamos que considerar la creación y eliminación de contextos cuando las estructuras de control solo tienen una instrucción (sin llaves).
    # No obstante, el profe nos limitó el alcance a solo bloques con llaves, por lo que no vamos a implementar este comportamiento adicional.

    def enterBloque(self, ctx):
        self.TS.addContexto()

    def exitBloque(self, ctx):
        self.TS.delContexto()

    def enterIfor(self, ctx): # Esto hay que hacerlo sí o sí porque el 'for' admite declaraciones en la sección init y no hacerlo provocaría que esas variables se carguen en el contexto global.
        self.TS.addContexto()
        # Hacer esto provoca que se generen 2 contextos anidados en los 'for' con llaves. 
        # No obstante, esto es correcto a nivel teórico (por el scope de las variables) y facilita la depuración.

    def exitIfor(self, ctx):
        self.TS.delContexto()

    # -----------------------------------
    # ---------- Manejo de IDs ----------
    # -----------------------------------

    def enterDeclaracion(self, ctx:compiladorParser.DeclaracionContext):
        pass

    def exitDeclaracion(self, ctx:compiladorParser.DeclaracionContext):
        # Una declaración es en realidad una lista de éstas, separadas por comas, que además pueden incluir una inicialización.
        # Por esta razón, no podemos hacer una lectura que simplemente tome el tipoDato + nombre e inmediatamnete agregue el símbolo a la tabla.

        # --- Lectura de la instrucción ---
        tipo = ctx.expDEC().tipo().getText() # Aparece una sola vez y es compartido por todas las declaraciones de la línea

        # Desgloce de la instrucción
        declaraciones = ctx.getText() # Cargamos TODOS los nodos del subárbol que conforman la declaración. Ej: declaraciones <-- "int x = 10, y, z = 0";
        declaraciones = declaraciones.replace(tipo,'').replace(';','').strip() # Limpiamos la línea y nos quedamos únicamente con los nombres de las variables y las posibles inicializaciones, separadas por ','. Ej: declaraciones <-- "x = 10, y, z = 0"
        declaraciones = [declaracion.strip() for declaracion in declaraciones.split(',')] # Convertimos el texto de las declaraciones en efectivamente una List de declaraciones, separando el texto orignal en las ','. Ej: declaraciones <-- ["x = 10", "y", "z = 0"]

        # --- Procesamiento de las declaraciones y generación de símbolos ---
        # Llegados a este punto, tenemos una lista de declaraciones de variables, pero todavía NO sabemos si están inicializadas
        # Además, hay que controlar si el símbolo ya estaba en la TS, en cuyo caso hay que reportar un error
        for declaracion in declaraciones :
            # Tenemos 2 tipos: inicializadas y no inicializadas
            if '=' in declaracion : 
                nombre, valor = [term.strip() for term in declaracion.split('=')] # No podemos usar '()' porque sería un generador
                qInit = True
            else :
                nombre = declaracion.strip()
                qInit = False # Redundante, pero no está demás ser explícito

            # Verificación de que en el contexto actual aún se permitan declaraciones
            contexto_actual = self.TS.contextos[-1]
            if not contexto_actual.canDeclarar():
                self.registrarError(TipoError.SEMANTICO, f"Declaraciones no permitidas en este punto ('{nombre}').")
                continue

            # Carga en la TS (vemos primero si ya existía)
            if(self.TS.buscarSimboloContexto(nombre)) : # El símbolo ya existe
                self.registrarError(TipoError.SEMANTICO, f"'{nombre}' ya existe en el contexto.")
            else :
                # Creación del símbolo
                nuevaVar = Variable(nombre,tipo)
                nuevaVar.inicializado = qInit
                # Carga en la TS
                self.TS.addSimbolo(nuevaVar)

        # Una vez procesadas las declaraciones de esta instrucción seguimos permitiendo declaraciones hasta que aparezca la primera instrucción que no sea una declaración.
        # Este evento es detectado por exitInstruccion().

    def exitInstruccion(self, ctx:compiladorParser.InstruccionContext):
        """Si la instrucción actual NO es una declaración, cerramos la posibilidad de declarar en el contexto actual (las declaraciones solo se permiten al principio)."""
        # ANTLR genera una clase InstruccionContext con métodos para obtener el contexto (subárbol) de cada subregla que aparece como alternativa en la producción.
        # Si la alternativa está presente en el árbol, el método correspondiente devuelve el contexto hijo; si no está presente, devuelve None.
        if ctx.declaracion() is None: # Por lo explicado antes, esto controla si la instrucción es una declaración o no
            if self.TS.contextos:
                self.TS.contextos[-1].forbidDeclaraciones()

    def exitPrototipo(self, ctx:compiladorParser.PrototipoContext): 
        # Quizás haya que ver esto con exitFuncion tmb
        pass

    # ---------------------------
    # ---------- Otros ----------
    # ---------------------------

    def __str__(self):
        pass