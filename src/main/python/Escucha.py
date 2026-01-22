from compiladorParser import compiladorParser
from compiladorListener import compiladorListener

from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Context import Contexto
from tablaDeSimbolos.Funcion import Funcion
from tablaDeSimbolos.Variable import Variable

from Enumeraciones import TipoError
from Enumeraciones import CType
from EscuchaErroresSintacticos import EscuchaErroresSintacticos # Nos hace falta saber si hubo errores sintácticos para no imprimir la TS cuando salimos del programa
from antlr4 import ErrorNode, ParserRuleContext 

class Escucha(compiladorListener):

    def __init__(self, escuchaErroresSintacticos):
        super().__init__()
        self.ts = TS.getTS()  # Obtener la instancia de la tabla de símbolos
        self.huboErrores = False  # Bandera para indicar si hubo errores semánticos
        self.escuchaErroresSintacticos = escuchaErroresSintacticos
        # Los errores sintácticos se manejan en EscuchaErroresSintacticos
        self.leyendoDeclaracion = False # Bandera para evitar reporte de "uso sin inicializar" en exitFactorCore durante la lectura de declaraciones
        self.stackFactores = [] # Pila para almacenar los factores encontrados durante el análisis de una declaración
        self.stackLlamadas = [] # Pila para almacenar las llamadas a funciones
        self.stackReturns = [] # Pila para almacenar los returns a chequear al salir de la definición de una función
    
    def __str__(self):
        pass

    # ###########################################################################
    # Utilidades
    # ###########################################################################

    def registrarError(self, tipo : TipoError, msj : str):
        """Recibe un mensaje de error y lo imprime por consola. Además, marca que hubo errores en la compilación."""
        self.huboErrores = True
        print(f"ERROR {tipo}: {msj}")

    def comprobarExistenciaSimbolo(self, nombre: str) -> bool:
        """Recibe el nombre de un símbolo y verifica si existe en la TS. Si no existe, registra un error semántico. Devuelve True si existe, False en caso contrario."""
        simbolo = self.ts.buscarSimbolo(nombre)
        if(simbolo is None):
            self.registrarError(TipoError.SEMANTICO, f"La variable '{nombre}' no existe.")
            return False
        else:
            simbolo.setUsado()
            return True

    def obtenerTipoResultante(self, ctx: ParserRuleContext) -> CType:
        """Recibe una expresión en forma de contexto y devuelve el tipo de dato correspondiente como CType."""
        
        rama_derecha = ctx.getChild(1) # Puede derivar en vacío
        if rama_derecha.getChildCount() == 0 : # Si tiene un solo hijo no vacío, retorna su valor
            return ctx.getChild(0).tipo
        else: # Más de un hijo no vacío, tenemos que evaluar el tipo resultante
            tipoResultante = ctx.getChild(0).tipo
            while rama_derecha.getChildCount() > 0:
                tipo_leido = rama_derecha.getChild(1).tipo
                tipoResultante = self.combinarTipos(tipoResultante, tipo_leido)
                rama_derecha = rama_derecha.getChild(2) # Avanzamos al siguiente nodo derecho
            return tipoResultante

    def combinarTipos(self, tipo1: CType, tipo2: CType) -> CType:
        """Recibe dos tipos de datos y devuelve el tipo resultante de su combinación, según las reglas definidas."""
        if tipo1 == CType.UNDETERMINED or tipo2 == CType.UNDETERMINED:
            return CType.UNDETERMINED
        if tipo1 == CType.VOID or tipo2 == CType.VOID:
            self.registrarError(TipoError.SEMANTICO, "Operación inválida con tipo 'void'.")
            return CType.UNDETERMINED
        if tipo1.rank > tipo2.rank:
            return tipo1
        else:
            return tipo2
        
    def obtenerParams(self, ctx, nombre_funcion: str):
        """Recibe el contexto (nodo) de una lista de parámetros y devuelve una lista con tuplas (tipo: CType, nombre: str). En caso de error, devuelve lista vacía."""
        # lista_tipos = []
        # if ctx.getChildCount() > 0: # Si la lista de parámetros NO deriva en vacío
        #     if ctx.getText() == 'void': # Ej: f(void)
        #         lista_tipos.append(CType.VOID)
        #     elif 'void' in ctx.getText(): # Ej: f(int, void) o f(void, int)
        #         self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' tiene una declaración de parámetros inválida con 'void'.")
        #     else: # Ej: f(int, char, float)
        #         for i in range(ctx.getChildCount() // 2 + 1):
        #             tipo_param = ctx.getChild(2*i).tipo().getText() # Los tipos están en los hijos pares (0,2,4,...)
        #             lista_tipos.append(CType.fromStr(tipo_param))
        # else: # Ej: f()
        #     lista_tipos.append(CType.VOID) # Si no hay parámetros explícitos, se asume void
        # return lista_tipos  
    
        lista_args = []
        if ctx.getChildCount() > 0: # Si la lista de parámetros NO deriva en vacío
            if ctx.getText() == 'void': # Ej: f(void)
                lista_args.append((CType.VOID, None))
            elif 'void' in ctx.getText(): # Ej: f(int, void) o f(void, int)
                self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' tiene una declaración de parámetros inválida con 'void'.")
            else: # Ej: f(int, char, float) || f(int a, char, float b)
                for i in range(ctx.getChildCount() // 2 + 1):
                    tipo_param = ctx.getChild(2*i).tipo().getText() # Los tipos están en los hijos pares (0,2,4,...)
                    nombre_param = ctx.getChild(2*i).ID().getText() if ctx.getChild(2*i).ID() else None
                    lista_args.append((CType.fromStr(tipo_param), nombre_param))
        else: # Ej: f()
            lista_args.append((CType.VOID, None)) # Si no hay parámetros explícitos, se asume void
        return lista_args

    # ###########################################################################
    # Inicio
    # ###########################################################################

    def enterPrograma(self, ctx):
        # Limpiamos el archivo de contenido de la TS
        with open("ContenidoTS.txt", "w") as f:
            pass
        # Indicamos que empezamos el parsing
        print(" ------ Comienza el parsing ------ ")

    def exitPrograma(self, ctx:compiladorParser.ProgramaContext):
        # self.buscarVariablesNoUsadas()
    
        # Tenemos que imprimir la TS solo si no hubo errores sintácticos ni semánticos
        if self.huboErrores or self.escuchaErroresSintacticos.errores: # Lista NO vacía = True
            with open("ContenidoTS.txt", "w") as f:
                f.write("Imposible generar la TS: Se encontraron errores durante el parsing.\n")
        else: # Si no hubieron errores, imprimimos la TS
            self.ts.imprimirTS()
        print(" ------ Termina el parsing ------ ")
    
    # ###########################################################################
    # Manejo básico de la Tabla de Símbolos
    # ############################################################################

    # ------------ Creación de contextos ------------
    # Bloque estándar
    def enterBloque(self, ctx: compiladorParser.BloqueContext): # Cuando se llega a un '{'
        self.ts.addContexto()
    
    # Instrucciones de control
    def enterIfor(self, ctx: compiladorParser.IforContext): # Cuando se entra en un 'for'
        self.ts.addContexto()
        # Esto genera la creación de 2 contextos anidados en for con llaves, pero no es bug: el contexto del for es necesario para variables declaradas en la inicialización y la implementación respeta el scope de las variables en C.

    # Funciones 
    def enterListParamsDef(self, ctx: compiladorParser.ListParamsDefContext):
        # Necesitamos agregar un contexto y cargar los parámetros ANTES de procesar el cuerpo. Esto nos permite validar el uso de los parámetros dentro del cuerpo de la función
        self.ts.addContexto()
    
    # ------------ Eliminación de contextos ------------
    # Bloque estándar
    def exitBloque(self, ctx: compiladorParser.BloqueContext): # Cuando se llega a un '}'
        self.ts.delContexto()

        if ctx.parentCtx is not None and isinstance(ctx.parentCtx, compiladorParser.FuncionContext):
            # Si el bloque pertenece a una función, eliminamos el contexto extra
            self.ts.delContexto()

    # Instrucciones de control
    def exitIfor(self, ctx: compiladorParser.IforContext): # Cuando se sale de un 'for'
        self.ts.delContexto()
    
    # ------------ Agregado de símbolos tipo Variable ------------
    # Variable: (nombre, tipoDato, inicializado, usado)

    def enterExpDEC(self, ctx: compiladorParser.ExpDECContext):
        # Activamos la bandera para no considerar como uso sin inicializar las referencias que formen parte de los inicializadores en la misma linea
        self.leyendoDeclaracion = True
        self.stackFactores.clear() # Limpiamos la pila de factores antes de empezar a leer la declaración
        
    def exitExpDEC(self, ctx: compiladorParser.ExpDECContext):
        # expDEC: tipo ID inic listavar 

        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            # Si hay un error de sintaxis en la declaración, no tiene sentido seguir
            return
        
        # ----------- Lectura de la instrucción -----------
        # 1ro) Extraemos el tipo de dato, que es el mismo para todas las declaraciones en la instrucción
        tipo_dato = ctx.tipo().getText() 
        # 2do) Convertimos el texto plano de las declaraciones en una lista de declaraciones individuales (Ej: ["x=5", "y", "z=x+2"])
        declaraciones = ctx.getText().replace(tipo_dato,'').replace(';','').strip()
        declaraciones = [declaracion.strip() for declaracion in declaraciones.split(',')]

        #  ----------- Procesamiento de las declaraciones y generación de símbolos -----------
        for declaracion in declaraciones:
            # 1ro) Extraemos los datos de la declaración
            if '=' in declaracion: # Tipo 1: con inicialización
                nombre, inicializador = [term.strip() for term in declaracion.split('=')]
                inicializada = True
            else: # Tipo 2: sin inicialización
                nombre = declaracion
                inicializada = False
            
            # 2do) Vemos si el símbolo ya existe en el contexto actual
            if(self.ts.buscarSimboloContexto(nombre)):
                self.registrarError(TipoError.SEMANTICO, f"La variable '{nombre}' ya fue declarada en este contexto.")
                continue # Pasamos a la siguiente sin agregar nada a la TS
            
            # 3ro) Controlamos el inicializador
            if(inicializada):
                for factor in self.stackFactores:
                    self.comprobarExistenciaSimbolo(factor)
            self.stackFactores.clear() # Limpiamos la pila de factores para la próxima declaración
            
            # 4to) Creamos el símbolo y lo integramos a la TS
            tipo_dato = CType.fromStr(ctx.tipo().getText())
            nueva_variable = Variable(nombre, tipo_dato)
            if(inicializada):
                nueva_variable.setInicializado()
            self.ts.addSimbolo(nueva_variable)
            
        self.leyendoDeclaracion = False # Desactivamos la bandera luego de procesar toda la instrucción

    def exitListParamsDef(self, ctx: compiladorParser.ListParamsDefContext):
        lista_argumentos = self.obtenerParams(ctx, ctx.parentCtx.ID().getText())
        if not lista_argumentos:
            return 
        # Agregamos los parámetros como variables en el contexto de la función
        if not lista_argumentos == [(CType.VOID, None)]: # Caso especial: función sin parámetros
            for tipo, nombre in lista_argumentos:
                nueva_variable = Variable(nombre, tipo)
                nueva_variable.setInicializado()
                self.ts.addSimbolo(nueva_variable)

    # ------------ Agregado de símbolos tipo Funcion ------------
    # Funcion: (nombre, tipoDato, args: Optional, inicializado, usado)
    
    def exitPrototipo(self, ctx: compiladorParser.PrototipoContext):
        # prototipo: tipo ID PA listaparam PA
        
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            # Si hay un error de sintaxis en el prototipo, no tiene sentido seguir
            return
        
        nombre_funcion = ctx.ID().getText()

        if len(self.ts.contextos) != 1: # Vemos si estamos en el contexto global (único permitido para funciones)
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' solo puede ser declarada en el contexto global.")
            return  # Salimos sin agregar nada a la TS
        if self.ts.buscarSimbolo("main"): # Vemos si se está intentando prototipar después de main (inválido)
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' no puede ser prototipada después de 'main'.")
            return  # Salimos sin agregar nada a la TS
        if nombre_funcion == "main": # Vemos si se está intentando prototipar main (inválido)
            self.registrarError(TipoError.SEMANTICO, "La función 'main' no puede ser prototipada.")
            return  # Salimos sin agregar nada a la TS
        if(self.ts.buscarSimbolo(nombre_funcion)):
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' ya fue declarada.")
            return # Salimos sin agregar nada a la TS

        tipo_retorno = CType.fromStr(ctx.tipo().getText())
        lista_argumentos = self.obtenerParams(ctx.getChild(3), nombre_funcion) # El nodo de la lista es el hijo 3
        if not lista_argumentos:
            return # Hubo un error al procesar los parámetros, salimos sin agregar nada a la TS  
        lista_tipos = [tipo for tipo, _ in lista_argumentos]
        nueva_funcion = Funcion(nombre_funcion, tipo_retorno, lista_tipos)
        self.ts.addSimbolo(nueva_funcion)

    def enterFuncion(self, ctx: compiladorParser.FuncionContext):
        # Al entrar en una funcion, limpiamos la pila de returns
        self.stackReturns.clear()

    def exitFuncion(self, ctx: compiladorParser.FuncionContext):
        # funcion : tipo ID PA listParamsDef PC bloque ; 
        
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            # Si hay un error de sintaxis en la función, no tiene sentido seguir
            return
        
        nombre_funcion = ctx.ID().getText()
        existente = self.ts.buscarSimbolo(nombre_funcion)

        if len(self.ts.contextos) != 1: # Vemos si estamos en el contexto global (único permitido para funciones)
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' solo puede ser declarada en el contexto global.")
            return  # Salimos sin agregar nada a la TS
        if self.ts.buscarSimbolo("main"): # Estamos después de main
            if not existente: # Y la función no existe ==> No fue prototipada ==> Error
                self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' no fue prototipada.")
                return
        if existente is not None: # La función ya existe en la TS ==> Sólo existe un prototipo || Ya fue definida
            if existente.getInicializado(): # Inicializada == True ==> Ya fue definida (existe un cuerpo) ==> Error
                self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' ya fue definida.")
                return

        # Carga de la función en la TS
        tipo_retorno = CType.fromStr(ctx.tipo().getText())
        lista_argumentos = self.obtenerParams(ctx.getChild(3), nombre_funcion)
        if not lista_argumentos:
            return
        lista_tipos = [tipo for tipo, _ in lista_argumentos]

        if existente is not None:
            if tipo_retorno != existente.getTipoDato() or lista_tipos != existente.getListaArgs():
                self.registrarError(TipoError.SEMANTICO, f"La definición de la función '{nombre_funcion}' no coincide con su prototipo.")
                return
            existente.setInicializado()
            return # Con esto evitamos agregarla de nuevo si ya había un prototipo
        nueva_funcion = Funcion(nombre_funcion, tipo_retorno, lista_tipos)
        nueva_funcion.setInicializado()
        self.ts.addSimbolo(nueva_funcion)
        
        # Chequeo de los returns almacenados en la pila
        for tipo_retorno_recibido in self.stackReturns:
            if tipo_retorno != tipo_retorno_recibido:
                self.registrarError(TipoError.SEMANTICO, f"La instrucción 'return' en la función '{nombre_funcion}' tiene un error de tipo. Se esperaba '{tipo_retorno.name}', pero se recibió '{tipo_retorno_recibido.name}'.")
    
    # ###########################################################################
    # Otros chequeos de semántica
    # ###########################################################################
    
    def exitExpASIG(self, ctx: compiladorParser.ExpASIGContext):
        
        # Chequeo de uso de variables (IDs) en el término de la IZQUIERDA
        nombre_id = ctx.ID().getText()
        self.comprobarExistenciaSimbolo(nombre_id)

    def exitFactorCore(self, ctx: compiladorParser.FactorCoreContext):

        # Tipo por defecto (CLAVE)
        ctx.tipo = CType.UNDETERMINED
        
        # Chequeo de uso de variables (IDs) en el término de la DERECHA
        if ctx.ID(): # Si el factor es un ID
            nombre_id = ctx.ID().getText()
            if not self.leyendoDeclaracion:
                if(self.comprobarExistenciaSimbolo(nombre_id)):
                    ctx.tipo = self.ts.buscarSimbolo(nombre_id).getTipoDato() # Asignamos el tipo del ID al contexto actual
                else:
                    ctx.tipo = CType.UNDETERMINED # Tipo indeterminado si no existe el símbolo
            else:
                self.stackFactores.append(nombre_id)
        
        # Asignación de tipo a literales y expresiones
        if ctx.NUMERO():
            ctx.tipo = CType.FLOAT if '.' in ctx.NUMERO().getText() else CType.INT
        if ctx.CARACTER():
            ctx.tipo = CType.CHAR
        if ctx.PA():
            ctx.tipo = ctx.exp().tipo # El tipo de dato de una expresión entre paréntesis es el tipo de dato de la expresión misma
        if ctx.llamadaFunc():
            pass
        
    def exitFactor(self, ctx: compiladorParser.FactorContext):
        # Propagación del tipo desde el FactorCore al Factor
        ctx.tipo = ctx.factorSufix().factorCore().tipo
        
    def exitTerm(self, ctx: compiladorParser.TermContext):
        # Propagación del tipo desde los factores al término
        ctx.tipo = self.obtenerTipoResultante(ctx)
        
    def exitExp(self, ctx: compiladorParser.ExpContext):
        # Propagación del tipo desde los términos a la expresión
        ctx.tipo = self.obtenerTipoResultante(ctx)
        
    def exitExpCOMP(self, ctx: compiladorParser.ExpCOMPContext):
        # Propagación del tipo desde las expresiones a la expresión de comparación
        ctx.tipo = self.obtenerTipoResultante(ctx)
        
    def exitExpIGUALDAD(self, ctx: compiladorParser.ExpIGUALDADContext):
        # Propagación del tipo desde las expresiones de comparación a la expresión de igualdad
        ctx.tipo = self.obtenerTipoResultante(ctx)
        
    def exitExpAND(self, ctx: compiladorParser.ExpANDContext):
        # Propagación del tipo desde las expresiones igualdad a la expresión AND
        ctx.tipo = self.obtenerTipoResultante(ctx)
        
    def exitExpOR(self, ctx: compiladorParser.ExpORContext):
        # Propagación del tipo desde las expresiones AND a la expresión OR
        ctx.tipo = self.obtenerTipoResultante(ctx)

    def exitOpal(self, ctx: compiladorParser.OpalContext):
        # Propagación del tipo desde el hijo único al nodo de la operación
        ctx.tipo = ctx.getChild(0).tipo

    # Control de tipos de datos compatibles
    def exitLlamadaFunc(self, ctx: compiladorParser.LlamadaFuncContext):
        
        funcion = self.ts.buscarSimbolo(ctx.getChild(0).getText())

        if funcion is None:
            self.registrarError(TipoError.SEMANTICO, f"La función '{ctx.getChild(0).getText()}' no existe.")
            return

        if not funcion.getInicializado():
            self.stackLlamadas.append(ctx) # Guardamos la llamada para procesar al final si se definió la función más tarde
        
        lista_tipos_esperados = funcion.getListaArgs()
        
        if len(lista_tipos_esperados) != (ctx.getChild(2).getChildCount() // 2 + 1):
            self.registrarError(TipoError.SEMANTICO, f"La llamada a la función '{funcion.getNombre()}' tiene un error en la cantidad de parámetros. Se esperaban {len(lista_tipos_esperados)} parámetros, pero se recibieron {ctx.getChild(2).getChildCount()}.")
        else: # Chequeo de tipos de cada parámetro
            for i, tipo_esperado in enumerate(lista_tipos_esperados):
                tipo_recibido = ctx.getChild(2).getChild(2*i).tipo
                if tipo_esperado != tipo_recibido:
                    self.registrarError(TipoError.SEMANTICO, f"La llamada a la función '{funcion.getNombre()}' tiene un error en el tipo del parámetro {i+1}. Se esperaba '{tipo_esperado.name}', pero se recibió '{tipo_recibido.name}'.")
            
    def exitIreturn(self, ctx: compiladorParser.IreturnContext):
        # funcion -> bloque -> instrucciones -> (instrucciones)* -> instruccion -> ireturn  
        # Revisamos si está dentro de una función
        ancestro = ctx
        while ancestro is not None and not isinstance(ancestro, compiladorParser.FuncionContext):
            ancestro = ancestro.parentCtx
        if ancestro is None:
            self.registrarError(TipoError.SEMANTICO, "La instrucción 'return' debe estar dentro de una función.")
            return
        
        # Obtenemos el tipo de retorno de la instrucción
        if isinstance(ctx.getChild(1), compiladorParser.OpalContext):
            tipo_retorno = ctx.getChild(1).tipo
        else:
            tipo_retorno = CType.VOID

        # Comparación con el tipo esperado
        funcion_actual = self.ts.buscarSimbolo(ancestro.ID().getText())
        if funcion_actual is None: # La función no existe ==> Puede que estemos en una definicion sin prototipo
            # Agregar a una pila para chequear el tipo cuando salimos de la definición
            self.stackReturns.append(tipo_retorno)
        else:
            tipo_retorno_esperado = funcion_actual.getTipoDato()
            if tipo_retorno != tipo_retorno_esperado:
                self.registrarError(TipoError.SEMANTICO, f"La instrucción 'return' en la función '{funcion_actual.getNombre()}' tiene un error de tipo. Se esperaba '{tipo_retorno_esperado.name}', pero se recibió '{tipo_retorno.name}'.")