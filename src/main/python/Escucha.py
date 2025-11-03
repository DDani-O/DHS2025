from compiladorParser import compiladorParser
from compiladorListener import compiladorListener
from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Variable import Variable
from tablaDeSimbolos.Funcion import Funcion
from Enumeraciones import TipoError
from antlr4 import ErrorNode

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
        self.buscarVariablesNoUsadas()
    
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
    # En C, la creación de contextos no se limita únicamente a contextos en bloques con llave, sino que también se crean contextos en estructuras de control y en funciones (esto lo tratamos en la sección de manejo de funciones).
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

    # -----------------------------------------
    # ---------- Manejo de Variables ----------
    # -----------------------------------------

    def exitDeclaracion(self, ctx:compiladorParser.DeclaracionContext):
        # Una declaración es en realidad una lista de éstas, separadas por comas, que además pueden incluir una inicialización.
        # Por esta razón, no podemos hacer una lectura que simplemente tome el tipoDato + nombre e inmediatamnete agregue el símbolo a la tabla.

        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            # Si hay un ErrorNode el error se registró con el EscuchaErroresSintacticos
            # No se puede procesar esta declaración, así que nos la saltamos
            return

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

    def exitInitialize(self, ctx:compiladorParser.InitializeContext):
        """Procesa declaraciones dentro de la sección init del for. La gramática recoge las declaraciones como expDEC (sin el ';'), por lo que hay que crear los símbolos de otra forma."""
        # Si no hay expDEC, no hay declaraciones, sino asignaciones
        if ctx.expDEC() is None:
            return

        # Si hay error sintáctico, no procesar
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        expdec = ctx.expDEC()
        tipo = expdec.tipo().getText()

        # Obtener el texto de la inicialización (p. ej. "int i = 0, j = 1") y procesar como en exitDeclaracion
        declaraciones = expdec.getText()
        declaraciones = declaraciones.replace(tipo, '').strip()
        # listavar no contiene ';', así que las comas separan las declaraciones
        declaraciones = [d.strip() for d in declaraciones.split(',') if d.strip()]

        for declaracion in declaraciones:
            if '=' in declaracion:
                nombre, valor = [t.strip() for t in declaracion.split('=', 1)]
                qInit = True
            else:
                nombre = declaracion.strip()
                qInit = False

            contexto_actual = self.TS.contextos[-1]
            if not contexto_actual.canDeclarar():
                self.registrarError(TipoError.SEMANTICO, f"Declaraciones no permitidas en este punto ('{nombre}').")
                continue

            if self.TS.buscarSimboloContexto(nombre):
                self.registrarError(TipoError.SEMANTICO, f"'{nombre}' ya existe en el contexto.")
            else:
                nuevaVar = Variable(nombre, tipo)
                nuevaVar.inicializado = qInit
                self.TS.addSimbolo(nuevaVar)

        # Igual que en exitDeclaracion, las declaraciones siguen permitidas hasta la primera instrucción no declarativa.

    def exitInstruccion(self, ctx:compiladorParser.InstruccionContext):
        """Si la instrucción actual NO es una declaración, cerramos la posibilidad de declarar en el contexto actual (las declaraciones solo se permiten al principio)."""
        # ANTLR genera una clase InstruccionContext con métodos para obtener el contexto (subárbol) de cada subregla que aparece como alternativa en la producción.
        # Si la alternativa está presente en el árbol, el método correspondiente devuelve el contexto hijo; si no está presente, devuelve None.
        if ctx.declaracion() is None: # Por lo explicado antes, esto controla si la instrucción es una declaración o no
            if self.TS.contextos:
                self.TS.contextos[-1].forbidDeclaraciones()


    # ---------------------------
    # ---------- Otros ----------
    # ---------------------------

    def exitExpASIG(self, ctx:compiladorParser.ExpASIGContext):
        # expASIG : ID ASIG opal ;  -> verificar que la variable izquierda esté declarada
        # Si hay ErrorNode, ignora
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        nombre = ctx.ID().getText()
        simbolo = self.TS.buscarSimbolo(nombre)
        if simbolo is None:
            self.registrarError(TipoError.SEMANTICO, f"Uso de identificador no declarado '{nombre}'.")
            return
        
        tipo_destino = simbolo.getTipoDato()
        tipo_valor = self._tipoExp(ctx.opal())
        
        if tipo_valor and tipo_destino != tipo_valor:
            self.registrarError(TipoError.SEMANTICO, f"Tipo incompatible en asignación a '{nombre}': se esperaba '{tipo_destino}', pero se obtuvo '{tipo_valor}'.")
        
        # Marcar como inicializada (por la asignación)
        simbolo.setInicializado()

    def exitFactorCore(self, ctx:compiladorParser.FactorCoreContext):
        # factorCore : NUMERO | ID | PA exp PC | llamadaFunc
        # Aparece cuando se usa un ID en una expresión -- verificar existencia
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        # Si tiene ID como hijo
        try:
            id_token = ctx.ID()
        except Exception:
            id_token = None

        if id_token is not None and id_token.getText() is not None:
            nombre = id_token.getText()
            simbolo = self.TS.buscarSimbolo(nombre)
            if simbolo is None:
                self.registrarError(TipoError.SEMANTICO, f"Uso de identificador no declarado '{nombre}'.")
                return
            # Marcar como usada (lectura)
            if not simbolo.getInicializado():
                self.registrarError(TipoError.SEMANTICO, f"Variable '{nombre}' usada sin inicializar.")
            simbolo.setUsado()

    def tipoExp(self, ctx):
        if ctx is None:
            return None
        
        if hasattr(ctx, 'ID') and ctx.ID():
            nombre = ctx.ID().getText()
            var = self.buscarExistenciaVariable(nombre)
            if var is None:
                return None
            var.setUsado()
            if not var.getInicializado():
                self.registrarError(TipoError.SEMANTICO, f"Variable '{nombre}' usada sin inicializar.")
            return var.getTipoDato()
        
        if hasattr(ctx, 'NUMERO') and ctx.NUMERO():
            return "int"
        
        tipos = set()
        for i in range(ctx.getChildCount()):
            tipo_hijo = self.tipoExp(ctx.getChild(i))
            if tipo_hijo:
                tipos.add(tipo_hijo)

        if len(tipos) == 1:
            return tipos.pop()
        elif len(tipos) > 1:
            self.registrarError(TipoError.SEMANTICO, "Tipos incompatibles en la expresión.")
            return None
        else:   
            return None
        
    def buscarVariablesNoUsadas(self):
        for index, contexto in enumerate(self.TS.historialCTX):
            for nombre, simbolo in contexto.simbolos.items():
                if not simbolo.getUsado():
                    self.registrarError(TipoError.SEMANTICO, f"Variable '{nombre}' declarada pero no utilizada.")
    
    def buscarExistenciaVariable(self, nombre):
        simbolo = self.TS.buscarSimbolo(nombre)
        if simbolo is None:
            self.registrarError(TipoError.SEMANTICO, f"Uso de identificador no declarado '{nombre}'.")
            return None
        return simbolo
    
    def __str__(self):
        pass