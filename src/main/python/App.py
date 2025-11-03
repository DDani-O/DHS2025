import sys
from antlr4 import *
from compiladorLexer  import compiladorLexer
from compiladorParser import compiladorParser
from Escucha import Escucha
from EscuchaErroresSintacticos import EscuchaErroresSintacticos
from Caminante import Caminante

# En caso de no poder ejecutar el programa Python por
# problemas de version (error ATNdeserializer), se
# pueden generar los archivos a mano.
#
# Ir a la carpeta donde esta el archivo .g4 y ejecutar 
#     antlr4 -Dlanguage=Python3 -visitor compilador.g4 -o .

def main(argv):
    # Entradas de testing
    archivo = "input/entradaConErrores.txt"
    # archivo = "input/entradaCorrecta.txt"

    if len(argv) > 1 :
        archivo = argv[1]
    input = FileStream(archivo)
    lexer = compiladorLexer(input)
    stream = CommonTokenStream(lexer)
    parser = compiladorParser(stream)

    # Eliminación del ErrorListener por defecto
    parser.removeErrorListeners()
    escuchaErroresSintacticos = EscuchaErroresSintacticos()
    parser.addErrorListener(escuchaErroresSintacticos)

    escucha = Escucha()
    parser.addParseListener(escucha)

    tree = parser.programa()

    # visitante = Caminante()
    # visitante.visitPrograma(tree)
    
    # print(escucha)
    # print(tree.toStringTree(recog=parser))

if __name__ == '__main__':
    main(sys.argv)