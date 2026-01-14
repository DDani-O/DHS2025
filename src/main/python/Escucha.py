from compiladorParser import compiladorParser
from compiladorListener import compiladorListener

from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Context import Contexto
from tablaDeSimbolos.Variable import Variable

from Enumeraciones import TipoError
from EscuchaErroresSintacticos import EscuchaErroresSintacticos # Nos hace falta saber si hubo errores sintácticos para no imprimir la TS cuando salimos del programa
from antlr4 import ErrorNode, ParserRuleContext 

class Escucha(compiladorListener):

    def __init__(self):
        super().__init__()
        self.ts = TS.getTS()  # Obtener la instancia de la tabla de símbolos
        self.huboErrores = False  # Bandera para indicar si hubo errores semánticos
        # Los errores sintácticos se manejan en EscuchaErroresSintacticos
        self.leyendoDeclaracion = False # Bandera para evitar reporte de "uso sin inicializar" en exitFactorCore durante la lectura de declaraciones
        self.stackFactores = [] # Pila para almacenar los factores encontrados durante el análisis de una declaración

    def __str__(self):
        pass

    # ###########################################################################
    # Utilidades
    # ###########################################################################

    def registrarError(self, tipo : TipoError, msj : str):
        """Recibe un mensaje de error y lo imprime por consola. Además, marca que hubo errores en la compilación."""
        self.huboErrores = True
        print(f"ERROR {tipo}: {msj}")

    def comprobarExistenciaSimbolo(self, nombre: str):
        simbolo = self.ts.buscarSimbolo(nombre)
        if(simbolo is None):
            self.registrarError(TipoError.SEMANTICO, f"La variable '{nombre}'no existe.")
        else:
            simbolo.setUsado()

    def obtenerTipoDato(self, expresion: str) -> str:
        pass

    def tiposCompatibles(self, tipo1: str, tipo2: str) -> bool:
        pass
    
    # def buscarFactorCores(self, ctx: ParserRuleContext):
    #     """Recorre recursivamente el subárbol sintáctico a partir del contexto que se le pase y devuelve una lista con todos los nodos FactorCoreContext encontrados."""
    #     result = [] # Acumula los FactorCores encontrados
    #     # Paso 1: verificamos si el context actual es factorCore
    #     if isinstance(ctx, compiladorParser.FactorCoreContext):
    #         result.append(ctx) # Si encontramos un FactorCore, lo agregamos a la lista
    #     # Paso 2: recorremos todos los hijos del context
    #     for child in ctx.getChildren():
    #         if isinstance(child, ParserRuleContext):
    #             # Llamada recursiva: exploramos los descendientes y nos traemos los FactorCores que encontremos
    #             result.extend(self.buscarFactorCores(child)) # Extend fusiona listas elemento a elemento
    #     # Paso 3: devolvemos la lista de factorCore encontrados
    #     return result
    
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
        if self.huboErrores or EscuchaErroresSintacticos.errores: # Lista NO vacía = True
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
    def enterBloque(self, ctx): # Cuando se llega a un '{'
        self.ts.addContexto()
    
    # Instrucciones de control
    def enterIfor(self, ctx): # Cuando se entra en un 'for'
        self.ts.addContexto()
        # Esto genera la creación de 2 contextos anidados en for con llaves, pero no es bug: el contexto del for es necesario para variables declaradas en la inicialización y la implementación respeta el scope de las variables en C.
    
    # ------------ Eliminación de contextos ------------
    # Bloque estándar
    def exitBloque(self, ctx): # Cuando se llega a un '}'
        self.ts.delContexto()

    # Instrucciones de control
    def exitIfor(self, ctx): # Cuando se sale de un 'for'
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
                # 3.1) Chequeamos la existencia de variables usadas en el inicializador
                for factor in self.stackFactores:
                    self.comprobarExistenciaSimbolo(factor)
                    
            #     # 3.2) Chequeamos compatibilidad de tipos
            #     tipo_inicializador = self.obtenerTipoDato(inicializador)
            #     if not self.tiposCompatibles(tipo_dato, tipo_inicializador):
            #         self.registrarError(TipoError.SEMANTICO, f"Incompatibilidad de tipos al inicializar la variable '{nombre}'. Se esperaba un valor de tipo '{tipo_dato}' pero se recibió '{tipo_inicializador}'.")
            #         continue # Pasamos a la siguiente sin agregar nada a la TS
            
            # 4to) Creamos el símbolo y lo integramos a la TS
            nueva_variable = Variable(nombre, tipo_dato)
            if(inicializada):
                nueva_variable.setInicializado()
            self.ts.addSimbolo(nueva_variable)
            
        self.leyendoDeclaracion = False # Desactivamos la bandera luego de procesar toda la instrucción

    # ------------ Agregado de símbolos tipo Funcion ------------
    # Funcion: (nombre, tipoDato, args: Optional, inicializado, usado)
        
    def exitPrototipo(self, ctx: compiladorParser.PrototipoContext):
        pass

    # ###########################################################################
    # Otros chequeos de semántica
    # ###########################################################################

    # def exitOpal(self, ctx: compiladorParser.OpalContext):
    #     factor_cores = self.buscarFactorCores(ctx)
    #     for fc in factor_cores:
    #         print("Factor encontrado:", fc.getText())

    def exitFactorCore(self, ctx: compiladorParser.FactorCoreContext):

        # Chequeo de uso de variables (IDs) en el término de la DERECHA
        if ctx.ID(): # Si el factor es un ID
            nombre_id = ctx.ID().getText()
            if not self.leyendoDeclaracion:
                self.comprobarExistenciaSimbolo(nombre_id)
            else:
                self.stackFactores.append(nombre_id)

    def exitExpASIG(self, ctx: compiladorParser.ExpASIGContext):
        
        # Chequeo de uso de variables (IDs) en el término de la IZQUIERDA
        nombre_id = ctx.ID().getText()
        self.comprobarExistenciaSimbolo(nombre_id)