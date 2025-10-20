from compiladorParser import compiladorParser
from compiladorListener import compiladorListener
from tablaDeSimbolos.SymbolTable import TS

class Escucha(compiladorListener) :
    # Esta clase personalizada la creamos porque el Listener original
    # se sobreescribe cada vez que se vuelve a generar el parser.
    # Con esto podemos definir los metodos que nos interesen y que 
    # permanezcan.

    declaracion = 0

    def __init__(self):
        super().__init__()
        self.TS = TS()
    
    # Inicio del programa

    def enterPrograma(self, ctx:compiladorParser.ProgramaContext):
        print("Comienza el parsing")

    def exitPrograma(self, ctx:compiladorParser.ProgramaContext):
        print("Termina el parsing")

    # Trabajo con contextos

    def enterBloque(self, ctx):
        TS.addContexto()
        print("Contexto creado")

    def exitBloque(self, ctx):
        TS.delContexto()
        print("Contexto eliminado")

    # Trabajo con IDs

    def enterDeclaracion(self, ctx:compiladorParser.DeclaracionContext):
        self.declaracion += 1
        print("Declaracion -> [" + ctx.getText() + "]")
        print(" -- Cantidad de hijos = " + str(ctx.getChildCount()))

    def exitDeclaracion(self, ctx:compiladorParser.DeclaracionContext):
        print("Declaracion EXIT -> [" + ctx.getText() + "]")
        print(" -- Cantidad de hijos = " + str(ctx.getChildCount()))

    def __str__(self):
        return "Se hicieron: " + str(self.declaracion) + " declaraciones."