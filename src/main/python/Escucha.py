from compiladorParser import compiladorParser
from compiladorListener import compiladorListener
from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Variable import Variable

class Escucha(compiladorListener) :
    # Esta clase personalizada la creamos porque el Listener original se sobreescribe cada vez que se vuelve a generar el parser.
    # Con esto podemos definir los metodos que nos interesen y que permanezcan.

    declaracion = 0

    def __init__(self):
        super().__init__()
        self.TS = TS()
    
    # ---------- Inicio del programa ----------

    def enterPrograma(self, ctx:compiladorParser.ProgramaContext):
        print("Comienza el parsing")

    def exitPrograma(self, ctx:compiladorParser.ProgramaContext):
        print("Termina el parsing")

    # ---------- Manejo de contextos ----------

    def enterBloque(self, ctx):
        TS.addContexto()
        print("Contexto creado")

    def exitBloque(self, ctx):
        TS.delContexto()
        print("Contexto eliminado")

    # ---------- Manejo de IDs ----------

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
            else :
                nombre = declaracion.strip()

            # Carga en la TS (vemos primero si ya existía)
            if(self.TS.buscarSimboloContexto(nombre)) : # El símbolo ya existe
                print("ERROR: '" + nombre + "' ya existe en el contexto.") # CAMBIAR POR UNA EXC
            else :
                # Creación del símbolo
                nuevaVar = Variable(nombre,tipo)
                nuevaVar.inicializado = True
                # Carga
                self.TS.addSimbolo(nuevaVar)

    def exitProtoripo(self, ctx:compiladorParser.PrototipoContext): 
        # Quizás haya que ver esto con exitFuncion tmb
        pass

    # ---------- Otros ----------

    def __str__(self):
        return "Se hicieron: " + str(self.declaracion) + " declaraciones."