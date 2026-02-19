import re

class Optimizador:
    def __init__(self):
        self.codigo = []

    def optimizar(self, archivo_entrada):
        """Recibe la dirección del archivo de código intermedio, lo carga y aplica optimizaciones iterativamente hasta que no se puedan hacer más cambios."""

        if not self.cargar_codigo(archivo_entrada) or len(self.codigo) == 0: # Lista vacía <=> Archivo vacío o no encontrado
            print("No hay código para optimizar.")
            return
        
        print("OPTIMIZANDO CÓDIGO INTERMEDIO...")
        iteracion = 1
        while True:
            print(f"Iteración {iteracion}")
            resultado1 = self.plegado_constantes()
            resultado2 = self.propagacion_copia()
            resultado3 = self.eliminacion_codigo_muerto()

            if not (resultado1 or resultado2 or resultado3): # Si no se hicieron cambios, terminamos
                print("No se realizaron más cambios. Terminando optimización...")
                break
            iteracion += 1

    def cargar_codigo(self, archivo_entrada):
        """Lee el archivo y devuelve True si se pudo cargar correctamente, o False si hubo un error."""
        try:
            with open(archivo_entrada, "r") as f:
                self.codigo = [linea.strip() for linea in f.readlines()]
            return True
        except FileNotFoundError:
            self.codigo = []
            print(f"ERROR: '{archivo_entrada}' no encontrado.")
            return False
        except Exception as e:
            self.codigo = []
            print(f"ERROR al cargar el archivo: {e}")
            return False

    def imprimir_codigo_optimizado(self, archivo_salida):
        with open(archivo_salida, "w") as f:
            for linea in self.codigo:
                f.write(linea + "\n")
        print(f"Código optimizado guardado en '{archivo_salida}'.")

    # ---------------- Plegado de constantes ----------------
    # Se evalúan expresiones constantes en tiempo de compilación y se reemplazan por su resultado
    # Ej: t1 = 2 + 3  --> t1 = 5
    def plegado_constantes(self):
        pass

    # ---------------- Propagación de copia ----------------
    # Se eliminan temporales intermedias cuando es seguro
    def propagacion_copia(self):
        pass

    # ---------------- Eliminación de código muerto ----------------
    # Se eliminan instrucciones que no afectan el resultado del programa, como asignaciones a variables que nunca se usan
    def eliminacion_codigo_muerto(self):
        pass