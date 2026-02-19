import re

# ###########################################################################
# Reglas léxicas para reconocer patrones de código intermedio
# ###########################################################################

ID = r'[a-zA-Z_][a-zA-Z0-9_]*' # Identificadores (variables, temporales, etiquetas)
NUM = r'-?\d+(?:\.\d+)?' # Números enteros o decimales, con opcional signo negativo
OP_BIN = r'==|!=|>=|<=|&&|\|\||[+\-*/%<>]' # Operadores binarios (comparación, lógica, aritmética)
OP_UNARIO = r'!' # Operadores unarios
# NOTA: Sólo tenemos en cuenta la negación porque es el único operador unario implementado. Si agregamos más, habría que considerarlos acá.

# t0 = 5 + 3 -> Plegado de constantes en operaciones binarias
REGEX_BINARIA_CONSTANTE = re.compile(fr'^({ID})\s*=\s*({NUM})\s*({OP_BIN})\s*({NUM})$')
# Grupos = (destino, op1, operador, op2)
# Grupos = ({ID}, {NUM}, {OP_BIN}, {NUM}), lo demás se descarta

# t0 = !5 -> Plegado de constantes en operaciones unarias
REGEX_UNARIA_CONSTANTE = re.compile(fr'^({ID})\s*=\s*({OP_UNARIO})\s*({NUM})$')
# Grupos = (destino, operador, operando)
# Grupos = ({ID}, {OP_UNARIO}, {NUM}), lo demás se descarta

# t0 = 5 -> Propagación de constante
REGEX_ASIGNACION_CONSTANTE = re.compile(fr'^({ID})\s*=\s*({NUM})$')
# Grupos = (destino, constante)
# Grupos = ({ID}, {NUM}), lo demás se descarta

# x = t0 -> Propagación de copia
REGEX_ASIGNACION_SIMPLE = re.compile(fr'^({ID})\s*=\s*({ID})$')
# Grupos = (destino, origen)
# Grupos = ({ID}, {ID}), lo demás se descarta

# ###########################################################################
# Optimizador de código intermedio
# ###########################################################################

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
        nuevo_codigo = []
        hubo_cambios = False

        for linea in self.codigo:
            # --- Binaria constante (t0 = 5 + 3) ---
            match = REGEX_BINARIA_CONSTANTE.match(linea)
            if match: # None si NO coincide
                destino, op1, operador, op2 = match.groups()
                val1 = float(op1)
                val2 = float(op2)
                resultado = None

                # Evaluamos la operación, manejando posibles errores, y guardamos el resultado para reemplazar la línea original por la optimizada
                try: # Para evitar que explote todo por errores en el código intermedio (como división por cero)
                    if operador == '+':
                        resultado = val1 + val2
                    elif operador == '-':
                        resultado = val1 - val2
                    elif operador == '*':
                        resultado = val1 * val2
                    elif operador == '/':
                        if val2 != 0:
                            resultado = val1 / val2
                        else:
                            raise ZeroDivisionError("División por cero")
                    elif operador == '%':
                        if val2 != 0:
                            resultado = val1 % val2
                        else:
                            raise ZeroDivisionError("Módulo por cero")
                    elif operador == '||':
                        resultado = 1 if (val1 != 0 or val2 != 0) else 0
                    elif operador == '&&':
                        resultado = 1 if (val1 != 0 and val2 != 0) else 0
                    elif operador == '==':
                        resultado = 1 if val1 == val2 else 0
                    elif operador == '!=':
                        resultado = 1 if val1 != val2 else 0
                    elif operador == '>':
                        resultado = 1 if val1 > val2 else 0
                    elif operador == '>=':
                        resultado = 1 if val1 >= val2 else 0
                    elif operador == '<':
                        resultado = 1 if val1 < val2 else 0
                    elif operador == '<=':
                        resultado = 1 if val1 <= val2 else 0
                    else:
                        nuevo_codigo.append(linea)
                        continue
                    
                    if resultado.is_integer():
                        resultado = int(resultado) # Para evitar resultados como 5.0
                    
                    nueva_linea = f"{destino} = {resultado}"
                    nuevo_codigo.append(nueva_linea)
                    hubo_cambios = True
                    continue
        
                except Exception as e: 
                    nuevo_codigo.append(linea) # Si hay algún error (ej: división por cero), no optimizamos esta línea
                    continue 

            # --- Unaria constante (t0 = !5) ---
            match = REGEX_UNARIA_CONSTANTE.match(linea)
            if match:
                destino, operador, operando = match.groups()
                val = float(operando)

                resultado = 0 if val != 0 else 1
                nueva_linea = f"{destino} = {resultado}"
                nuevo_codigo.append(nueva_linea)
                hubo_cambios = True
                continue

            # --- No hubo match de ningún tipo de plegado ---
            nuevo_codigo.append(linea) # Mantenemos la línea original

        # ----- Fin de la etapa ----- 
        self.codigo = nuevo_codigo # Actualizamos el código con el que trabaja el optimizador, para que las siguientes optimizaciones trabajen sobre el resultado de esta
        return hubo_cambios

    # ---------------- Propagación de copia ----------------
    # Se eliminan temporales intermedias cuando es seguro
    def propagacion_copia(self):
        pass

    # ---------------- Eliminación de código muerto ----------------
    # Se eliminan instrucciones que no afectan el resultado del programa, como asignaciones a variables que nunca se usan
    def eliminacion_codigo_muerto(self):
        pass