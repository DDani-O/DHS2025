from compiladorParser import compiladorParser
from compiladorListener import compiladorListener

from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Context import Contexto
from tablaDeSimbolos.Variable import Variable

from Enumeraciones import TipoError
from EscuchaErroresSintacticos import EscuchaErroresSintacticos # Nos hace falta saber si hubo errores sintácticos para no imprimir la TS cuando salimos del programa

class Escucha(compiladorListener):

    def __init__(self):
        super().__init__()
        self.ts = TS.getTS()  # Obtener la instancia de la tabla de símbolos
        self.huboErrores = False  # Bandera para indicar si hubo errores semánticos
        # Los errores sintácticos se manejan en EscuchaErroresSintacticos

    # ###########################################################################
    # Utilidades
    # ###########################################################################

    def registrarError(self, tipo : TipoError, msj : str):
        """Recibe un mensaje de error y lo imprime por consola. Además, marca que hubo errores en la compilación."""
        self.huboErrores = True
        print(f"ERROR {tipo}: {msj}")

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
        if self.huboErrores and EscuchaErroresSintacticos.errores: # Lista NO vacía = True
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

    def enterIwhile(self, ctx):
        self.ts.addContexto()

    def enterIif(self, ctx):
        self.ts.addContexto()
    
    # ------------ Eliminación de contextos ------------
    # Bloque estándar
    def exitBloque(self, ctx): # Cuando se llega a un '}'
        self.ts.delContexto()

    # Instrucciones de control
    def exitIfor(self, ctx): # Cuando se sale de un 'for'
        self.ts.delContexto()

    def enterIwhile(self, ctx):
        self.ts.delContexto()

    def enterIif(self, ctx):
        self.ts.delContexto()

    # ------------ Agregado de símbolos tipo Variable ------------

    # ------------ Agregado de símbolos tipo Funcion ------------
        # ToDo - No entra al TP3

    # ###########################################################################
    # Otros chequeos de semántica
    # ###########################################################################

    def __str__(self):
        pass