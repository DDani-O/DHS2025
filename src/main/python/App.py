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
    # archivo = "input/testerFunciones.txt"
    # archivo = "input/testerErroresSintacticos.txt"
    archivo = "input/entradaSimple.txt"
    # archivo = "input/entradaCorrecta.txt"
    # archivo = "input/entradaConErrores.txt"

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

    # Agregado del Listener personalizado para detectar errores semánticos
    escucha = Escucha()
    parser.addParseListener(escucha)

    # Inicio del parsing
    tree = parser.programa()

    if not escucha.huboErrores and not escuchaErroresSintacticos.errores:
        # Compilación sin errores, imprimimos la TS y generamos el código intermedio
        print("Entrada correcta. Generando archivos de salida...")

        # Impresión de la TS
        with open("output/ContenidoTS.txt", "w") as f:
            escucha.ts.imprimirTS(f)

        # Generación de código intermedio
        visitante = Caminante()
        visitante.visitPrograma(tree)

        # Impresión del código intermedio
        with open("output/CodigoIntermedio.txt", "w") as f:
            for linea in visitante.codigoIntermedio:
                f.write(linea + "\n")

        # Impresión de código optimizado
        # TODO: Implementar optimizaciones y generar un archivo de salida para el código optimizado

    else: # Si hubo errores, limpiamos los archivos de salida para evitar confusiones
        print("Entrada incorrecta. Limpiando archivos de salida...")
        with open("output/ContenidoTS.txt", "w") as f:
            f.write("Imposible generar la TS: Se encontraron errores durante el parsing.\n")
        with open("output/CodigoIntermedio.txt", "w") as f:
            f.write("Imposible generar el código intermedio: Se encontraron errores durante el parsing.\n")
        # TODO limpiar el archivo de código optimizado también, una vez que se implemente la generación de código optimizado

if __name__ == '__main__':
    main(sys.argv)