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

    def visitErrorNode(self, nodo : ErrorNode):
        """Captura errores sintácticos en el árbol y los reporta sin detener el parsing."""
        self.huboErrores = True
        texto_ErrorNode = nodo.getText()
        self.registrarError(TipoError.SINTACTICO, f"'{texto_ErrorNode}'")

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

        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            # Si hay un ErrorNode el error se registró en visitErrorNode()
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
        """Procesa declaraciones dentro de la sección init del for cuando vienen con tipo (expDEC).
        La gramática recoge las declaraciones como expDEC (sin el ';'), por lo que hay que crear los símbolos de otra forma.
        """
        # Si no hay expDEC, no hay declaraciones con tipo en la inicialización
        if ctx.expDEC() is None:
            return

        # Si hay error sintáctico, no procesar
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            self.registrarError(TipoError.SINTACTICO, "Formato incorrecto en la inicialización del for")
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

    def exitInstruccion(self, ctx:compiladorParser.InstruccionContext):
        """Si la instrucción actual NO es una declaración, cerramos la posibilidad de declarar en el contexto actual (las declaraciones solo se permiten al principio)."""
        # ANTLR genera una clase InstruccionContext con métodos para obtener el contexto (subárbol) de cada subregla que aparece como alternativa en la producción.
        # Si la alternativa está presente en el árbol, el método correspondiente devuelve el contexto hijo; si no está presente, devuelve None.
        if ctx.declaracion() is None: # Por lo explicado antes, esto controla si la instrucción es una declaración o no
            if self.TS.contextos:
                self.TS.contextos[-1].forbidDeclaraciones()

    def exitPrototipo(self, ctx:compiladorParser.PrototipoContext): 
        # Procesar un prototipo: tipo ID '(' listParamsProt? ')' ';'
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        tipo = ctx.tipo().getText()
        nombre = ctx.ID().getText()

        # Leer parámetros si existen (en los prototipos el nombre del parámetro es opcional)
        args = []
        if ctx.listParamsProt() is not None:
            # listParamsProt : parametroProt (COMA parametroProt)*
            for p in ctx.listParamsProt().parametroProt():
                # parametroProt : tipo | tipo ID
                t = p.tipo().getText()
                # Para prototipo no necesitamos el nombre, sólo el tipo. Crear Variable con nombre vacío
                args.append(Variable('', t))

        # Verificar si ya existe un símbolo con ese nombre en el contexto actual
        if self.TS.buscarSimboloContexto(nombre):
            self.registrarError(TipoError.SEMANTICO, f"Prototipo '{nombre}' ya existe en el contexto.")
            return

        # Crear y agregar el prototipo (inicializado=False)
        f = Funcion(nombre, tipo, args=args, inicializado=False)
        self.TS.addSimbolo(f)

    def enterFuncion(self, ctx:compiladorParser.FuncionContext):
        # Se ejecuta antes de procesar el bloque/los parámetros de la función.
        # Aquí: - comprobar existencia de prototipo (salvo 'main'),
        #       - crear/actualizar el símbolo de función en el contexto exterior,
        #       - crear el contexto local de la función y cargar los parámetros como variables locales.

        # Si hay ErrorNode en la cabecera, no procesar
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        tipo = ctx.tipo().getText()
        nombre = ctx.ID().getText()

        # Construir lista de args (para el símbolo) a partir de la definición (tienen nombre)
        args_for_symbol = []
        params = []
        if ctx.listParamsDef() is not None:
            for p in ctx.listParamsDef().parametroDef():
                t = p.tipo().getText()
                n = p.ID().getText()
                params.append((n, t))
                # Para la firma del símbolo nos interesa el tipo; el nombre del parámetro lo guardamos en la tabla local
                args_for_symbol.append(Variable(n, t))

        # Comprobar si hay prototipo/entrada previa
        simbolo_prev = self.TS.buscarSimbolo(nombre)
        if simbolo_prev is None:
            # Permitimos que 'main' no tenga prototipo
            if nombre != 'main':
                self.registrarError(TipoError.SEMANTICO, f"Definición de función '{nombre}' sin prototipo previo (símbolo desconocido).")
            # Crear el símbolo de función en el contexto actual (externo a la función)
            f = Funcion(nombre, tipo, args=args_for_symbol, inicializado=True)
            self.TS.addSimbolo(f)
            simbolo = f
        else:
            # Si existe y es función, marcar inicializado y actualizar firma si procede
            if isinstance(simbolo_prev, Funcion):
                simbolo_prev.setInicializado()
                # Si el prototipo no tenía args con nombres, actualizarlos desde la definición
                if simbolo_prev.getListaArgs() == [] and args_for_symbol:
                    simbolo_prev.args = args_for_symbol
                simbolo = simbolo_prev
            else:
                # Existe otro símbolo con ese nombre
                self.registrarError(TipoError.SEMANTICO, f"'{nombre}' fue declarado como otro tipo de símbolo y ahora se intenta definir como función.")
                # crear igualmente la función para seguir analizando
                f = Funcion(nombre, tipo, args=args_for_symbol, inicializado=True)
                self.TS.addSimbolo(f)
                simbolo = f

        # Ahora creamos el contexto LOCAL para la función y cargamos los parámetros como variables locales
        self.TS.addContexto()
        # Agregar parámetros al contexto local
        for n, t in params:
            # Parámetros se consideran inicializados
            nuevaVar = Variable(n, t)
            nuevaVar.inicializado = True
            self.TS.addSimbolo(nuevaVar)

    # ---------------------------
    # ---------- Otros ----------
    # ---------------------------

    def exitFuncion(self, ctx:compiladorParser.FuncionContext):
        # Al salir de la función eliminamos el contexto local creado en enterFuncion
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            # Si hubo errores sintácticos, simplemente limpiamos el contexto igualmente
            if self.TS.contextos:
                self.TS.delContexto()
            return

        # Eliminar contexto local de la función
        if self.TS.contextos:
            self.TS.delContexto()

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

        # Si existe y es Variable o Funcion (si alguien asigna a una función, es error)
        # Permitimos solo Variable
        from tablaDeSimbolos.Variable import Variable as VarClass
        if not isinstance(simbolo, VarClass):
            self.registrarError(TipoError.SEMANTICO, f"'{nombre}' no es una variable y no puede asignarse.")
            return

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
            simbolo.setUsado()

    def exitLlamadaFunc(self, ctx:compiladorParser.LlamadaFuncContext):
        # Manejar llamada a función: ID '(' listArgs? ')'
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        nombre = ctx.ID().getText()
        simbolo = self.TS.buscarSimbolo(nombre)
        if simbolo is None:
            self.registrarError(TipoError.SEMANTICO, f"Llamada a función desconocida '{nombre}'.")
            return

        if not isinstance(simbolo, Funcion):
            self.registrarError(TipoError.SEMANTICO, f"'{nombre}' no es una función.")
            return

        # Marcar como usada
        simbolo.setUsado()

    def __str__(self):
        pass