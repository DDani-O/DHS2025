from compiladorVisitor import compiladorVisitor
from compiladorParser import compiladorParser

class Caminante (compiladorVisitor) :
    def visitPrograma (self, ctx:compiladorParser.ProgramaContext):
        print("Programa procesado")
        return ctx