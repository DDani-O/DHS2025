from compiladorParser import compiladorParser
from compiladorListener import compiladorListener

from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Context import Contexto
from tablaDeSimbolos.Funcion import Funcion
from tablaDeSimbolos.Variable import Variable

from Enumeraciones import TipoError
from Enumeraciones import CType
from antlr4 import ErrorNode, ParserRuleContext 

class Escucha(compiladorListener):

    def __init__(self):
        super().__init__()
        self.ts = TS.getTS()  # Obtener la instancia de la tabla de símbolos
        self.huboErrores = False  # Bandera para indicar si hubo errores semánticos
        self.stackLlamadas = [] # Pila para almacenar las llamadas a funciones
        self.stackReturns = [] # Pila para almacenar los returns a chequear al salir de la definición de una función
        self.tipoADeclarar = None # Tipo de dato que se está declarando (usado en declaraciones múltiples)
    
    def __str__(self):
        pass

    # ###########################################################################
    # Utilidades
    # ###########################################################################

    def registrarError(self, tipo : TipoError, msj : str, ctx = None):
        """Recibe un mensaje de error y lo imprime por consola. Si se le pasa un contexto, también imprime la línea en que ocurrió el error. Luego marca que hubo errores en la compilación."""
        self.huboErrores = True
        if ctx is not None and hasattr(ctx, 'start'):
            linea = ctx.start.line
        else:
            linea = '?'
        print(f"ERROR {tipo} (ln {linea}): {msj}")

    def comprobarExistenciaSimbolo(self, nombre: str, ctx = None) -> bool:
        """Recibe el nombre de un símbolo, verifica si existe en la TS y, si no existe, registra un error semántico. Devuelve True si existe, False en caso contrario."""
        simbolo = self.ts.buscarSimbolo(nombre)
        if(simbolo is None):
            self.registrarError(TipoError.SEMANTICO, f"El identificador '{nombre}' no existe.", ctx)
            return False
        else:
            simbolo.setUsado()
            return True

    def obtenerTipoResultante(self, ctx: ParserRuleContext) -> CType:
        """Recibe una expresión en forma de contexto y devuelve el tipo de dato correspondiente como CType."""
        
        try:
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
        except AttributeError: # Este error salta en ramas incompletas por errores sintácticos
            return CType.UNDETERMINED

    def combinarTipos(self, tipo1: CType, tipo2: CType, ctx = None) -> CType:
        """Recibe dos tipos de datos y devuelve el tipo resultante de su combinación, según las reglas definidas."""
        if tipo1 == CType.UNDETERMINED or tipo2 == CType.UNDETERMINED:
            return CType.UNDETERMINED
        if tipo1 == CType.VOID or tipo2 == CType.VOID:
            self.registrarError(TipoError.SEMANTICO, "Operación inválida con tipo 'void'.", ctx)
            return CType.UNDETERMINED
        if tipo1.rank > tipo2.rank:
            return tipo1
        else:
            return tipo2
        
    def obtenerParams(self, ctx, nombre_funcion: str):
        """Recibe el contexto (nodo) de una lista de parámetros y devuelve una lista con tuplas (tipo: CType, nombre: str). En caso de error, devuelve lista vacía."""    
        lista_args = []
        if ctx.getChildCount() > 0: # Si la lista de parámetros NO deriva en vacío
            if ctx.getText() == 'void': # Ej: f(void)
                lista_args.append((CType.VOID, None))
            elif 'void' in ctx.getText(): # Ej: f(int, void) o f(void, int)
                self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' tiene una declaración de parámetros inválida con 'void'.", ctx)
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
        # Chequeo de llamadas a funciones no definidas
        for llamada in self.stackLlamadas:
            funcion = self.ts.buscarSimbolo(llamada.getChild(0).getText())
            if not funcion.getInicializado():
                self.registrarError(TipoError.SEMANTICO, f"La función '{funcion.getNombre()}' no fue definida.", llamada)
        
        # Chequeo de símbolos (de todo tipo) declarados pero no usados
        for contexto in self.ts.historialCTX:
            for nombre, simbolo in contexto.simbolos.items():
                if not simbolo.getUsado():
                    self.registrarError(TipoError.SEMANTICO, f"El símbolo ({"variable" if isinstance(simbolo, Variable) else "función"}) '{nombre}' fue declarado pero no fue usado.")
                    
        print(" ------ Termina el parsing ------ ")
    
    # ###########################################################################
    # Manejo básico de la Tabla de Símbolos
    # ############################################################################

    # ------------ Creación de contextos ------------
    # Bloque estándar
    def enterBloque(self, ctx: compiladorParser.BloqueContext): # Cuando se llega a un '{'
        self.ts.addContexto()
        if ctx.parentCtx is not None and isinstance(ctx.parentCtx, compiladorParser.FuncionContext):
            # Si el bloque pertenece a una función, cargamos sus parámetros
            self.cargarParametrosFuncion(ctx.parentCtx)
    
    # Instrucciones de control
    def enterIfor(self, ctx: compiladorParser.IforContext): # Cuando se entra en un 'for'
        self.ts.addContexto()
        # Esto genera la creación de 2 contextos anidados en for con llaves, pero no es bug: el contexto del for es necesario para variables declaradas en la inicialización y la implementación respeta el scope de las variables en C.
    
    # ------------ Eliminación de contextos ------------
    # Bloque estándar
    def exitBloque(self, ctx: compiladorParser.BloqueContext): # Cuando se llega a un '}'
        self.ts.delContexto()

    # Instrucciones de control
    def exitIfor(self, ctx: compiladorParser.IforContext): # Cuando se sale de un 'for'
        self.ts.delContexto()
    
    # ------------ Agregado de símbolos tipo Variable ------------
    # Variable: (nombre, tipoDato, inicializado, usado)
    def enterListaDeclaradores(self, ctx: compiladorParser.ListaDeclaradoresContext):
        self.tipoADeclarar = CType.fromStr(ctx.parentCtx.tipo().getText())

    def exitDeclarador(self, ctx: compiladorParser.DeclaradorContext):
        nombre_variable = ctx.ID().getText()
        if self.ts.buscarSimboloContexto(nombre_variable):
            self.registrarError(TipoError.SEMANTICO, f"La variable '{nombre_variable}' ya fue declarada en este contexto.", ctx)
            return
        nueva_variable = Variable(nombre_variable, self.tipoADeclarar)
        if ctx.inic().getChildCount() > 0:
            nueva_variable.setInicializado()
        self.ts.addSimbolo(nueva_variable)

    def cargarParametrosFuncion(self, ctx: compiladorParser.FuncionContext):
        """Recibe el contexto (nodo) de la funcion y carga sus parámetros como variables en el contexto de la función."""
        lista_argumentos = self.obtenerParams(ctx.listParamsDef(), ctx.ID().getText())
        if not lista_argumentos:
            return 
        # Agregamos los parámetros como variables en el contexto de la función
        if not lista_argumentos == [(CType.VOID, None)]: # Caso especial: función sin parámetros
            for tipo, nombre in lista_argumentos:
                nueva_variable = Variable(nombre, tipo)
                nueva_variable.setInicializado() # Parámetros siempre inicializados
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
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' solo puede ser declarada en el contexto global.", ctx)
            return  # Salimos sin agregar nada a la TS
        if self.ts.buscarSimbolo("main"): # Vemos si se está intentando prototipar después de main (inválido)
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' no puede ser prototipada después de 'main'.", ctx)
            return  # Salimos sin agregar nada a la TS
        if nombre_funcion == "main": # Vemos si se está intentando prototipar main (inválido)
            self.registrarError(TipoError.SEMANTICO, "La función 'main' no puede ser prototipada.", ctx)
            return  # Salimos sin agregar nada a la TS
        if(self.ts.buscarSimbolo(nombre_funcion)):
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' ya fue declarada.", ctx)
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
            self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' solo puede ser declarada en el contexto global.", ctx)
            return  # Salimos sin agregar nada a la TS
        if self.ts.buscarSimbolo("main"): # Estamos después de main
            if not existente: # Y la función no existe ==> No fue prototipada ==> Error
                self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' no fue prototipada.", ctx)
                return
        if existente is not None: # La función ya existe en la TS ==> Sólo existe un prototipo || Ya fue definida
            if existente.getInicializado(): # Inicializada == True ==> Ya fue definida (existe un cuerpo) ==> Error
                self.registrarError(TipoError.SEMANTICO, f"La función '{nombre_funcion}' ya fue definida.", ctx)
                return

        # Carga de la función en la TS
        tipo_retorno = CType.fromStr(ctx.tipo().getText())
        lista_argumentos = self.obtenerParams(ctx.getChild(3), nombre_funcion)
        if not lista_argumentos:
            return
        lista_tipos = [tipo for tipo, _ in lista_argumentos]

        if existente is not None:
            if tipo_retorno != existente.getTipoDato() or lista_tipos != existente.getListaArgs():
                self.registrarError(TipoError.SEMANTICO, f"La definición de la función '{nombre_funcion}' no coincide con su prototipo.", ctx)
                return
            existente.setInicializado()
            return # Con esto evitamos agregarla de nuevo si ya había un prototipo
        nueva_funcion = Funcion(nombre_funcion, tipo_retorno, lista_tipos)
        nueva_funcion.setInicializado()
        if nombre_funcion == "main":
            nueva_funcion.setUsado() # Main siempre se considera usada
        self.ts.addSimbolo(nueva_funcion)
        
        # Chequeo de los returns almacenados en la pila
        for tipo_retorno_recibido, ctx_return in self.stackReturns:
            if tipo_retorno != tipo_retorno_recibido:
                self.registrarError(TipoError.SEMANTICO, f"La instrucción 'return' en la función '{nombre_funcion}' tiene un error de tipo. Se esperaba '{tipo_retorno.name}', pero se recibió '{tipo_retorno_recibido.name}'.", ctx_return)

    # ###########################################################################
    # Otros chequeos de semántica
    # ###########################################################################
    
    def exitExpASIG(self, ctx: compiladorParser.ExpASIGContext):
        
        # Chequeo de uso de variables (IDs) en el término de la IZQUIERDA
        nombre_id = ctx.ID().getText()
        if self.comprobarExistenciaSimbolo(nombre_id, ctx):
            self.ts.buscarSimbolo(nombre_id).setInicializado() # Marcamos la variable como inicializada tras una asignación

    def exitFactorCore(self, ctx: compiladorParser.FactorCoreContext):

        # Tipo por defecto (CLAVE)
        ctx.tipo = CType.UNDETERMINED
        
        # Chequeo de uso de variables en el término de la DERECHA y asignación de tipo
        if ctx.ID():
            nombre_id = ctx.ID().getText()
            if self.comprobarExistenciaSimbolo(nombre_id, ctx):
                variable = self.ts.buscarSimbolo(nombre_id)
                ctx.tipo = variable.getTipoDato()
                if not variable.getInicializado():
                    self.registrarError(TipoError.SEMANTICO, f"La variable '{nombre_id}' fue usada sin ser inicializada.", ctx)
                variable.setUsado()
        
        # Asignación de tipo a literales y expresiones
        if ctx.NUMERO():
            ctx.tipo = CType.FLOAT if '.' in ctx.NUMERO().getText() else CType.INT
        if ctx.CARACTER():
            ctx.tipo = CType.CHAR
        if ctx.PA():
            ctx.tipo = ctx.exp().tipo # El tipo de dato de una expresión entre paréntesis es el tipo de dato de la expresión misma
        if ctx.llamadaFunc():
            ctx.tipo = ctx.llamadaFunc().tipo # El tipo de dato de una llamada a función es el tipo de dato retornado por la función
        
    def exitFactor(self, ctx: compiladorParser.FactorContext):
        # Propagación del tipo desde el FactorCore al Factor
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()) or ctx.factorSufix() is None or ctx.factorSufix().factorCore() is None: # Para que no explote por E Sintácticos
            ctx.tipo = CType.UNDETERMINED
        else:
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

    def exitLlamadaFunc(self, ctx: compiladorParser.LlamadaFuncContext):
        
        funcion = self.ts.buscarSimbolo(ctx.getChild(0).getText())

        if funcion is None:
            self.registrarError(TipoError.SEMANTICO, f"La función '{ctx.getChild(0).getText()}' no existe.", ctx)
            ctx.tipo = CType.UNDETERMINED
            return
        else:
            ctx.tipo = funcion.getTipoDato() # Asignamos el tipo de dato de la función al nodo

        if not funcion.getInicializado():
            self.stackLlamadas.append(ctx) # Guardamos la llamada para procesar al final si se definió la función más tarde
        
        # Control de tipos de datos compatibles
        lista_tipos_esperados = funcion.getListaArgs()
        
        if len(lista_tipos_esperados) != (ctx.getChild(2).getChildCount() // 2 + 1):
            self.registrarError(TipoError.SEMANTICO, f"La llamada a la función '{funcion.getNombre()}' tiene un error en la cantidad de parámetros. Se esperaban {len(lista_tipos_esperados)} parámetros, pero se recibieron {ctx.getChild(2).getChildCount()}.", ctx)
        else: 
            for i, tipo_esperado in enumerate(lista_tipos_esperados):
                argumento = ctx.getChild(2).getChild(2*i)
                # Chequeo de tipos de cada argumento
                tipo_recibido = argumento.tipo
                if tipo_esperado != tipo_recibido:
                    self.registrarError(TipoError.SEMANTICO, f"La llamada a la función '{funcion.getNombre()}' tiene un error en el tipo del parámetro {i+1}. Se esperaba '{tipo_esperado.name}', pero se recibió '{tipo_recibido.name}'.", ctx)

        funcion.setUsado()
            
    def exitIreturn(self, ctx: compiladorParser.IreturnContext):
        # funcion -> bloque -> instrucciones -> (instrucciones)* -> instruccion -> ireturn  
        # Revisamos si está dentro de una función
        ancestro = ctx
        while ancestro is not None and not isinstance(ancestro, compiladorParser.FuncionContext):
            ancestro = ancestro.parentCtx
        if ancestro is None:
            self.registrarError(TipoError.SEMANTICO, "La instrucción 'return' debe estar dentro de una función.", ctx)
            return
        # Control de tipos de datos compatibles
        # Obtenemos el tipo de retorno de la instrucción
        if isinstance(ctx.getChild(1), compiladorParser.OpalContext):
            tipo_retorno = ctx.getChild(1).tipo
        else:
            tipo_retorno = CType.VOID

        # Comparación con el tipo esperado
        funcion_actual = self.ts.buscarSimbolo(ancestro.ID().getText())
        if funcion_actual is None: # La función no existe ==> Puede que estemos en una definicion sin prototipo
            # Agregar a una pila para chequear el tipo cuando salimos de la definición
            self.stackReturns.append((tipo_retorno, ctx))
        else:
            tipo_retorno_esperado = funcion_actual.getTipoDato()
            if tipo_retorno != tipo_retorno_esperado:
                self.registrarError(TipoError.SEMANTICO, f"La instrucción 'return' en la función '{funcion_actual.getNombre()}' tiene un error de tipo. Se esperaba '{tipo_retorno_esperado.name}', pero se recibió '{tipo_retorno.name}'.", ctx)