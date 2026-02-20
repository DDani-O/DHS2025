import re

# ###########################################################################
# Reglas léxicas para reconocer patrones de código intermedio
# ###########################################################################

ID = r'[a-zA-Z_][a-zA-Z0-9_]*' # Identificadores (variables, temporales, etiquetas)
NUM = r'-?\d+(?:\.\d+)?' # Números enteros o decimales, con opcional signo negativo
OP_BIN = r'==|!=|>=|<=|&&|\|\||[+\-*/%<>]' # Operadores binarios (comparación, lógica, aritmética)
OP_UNARIO = r'!' # Operadores unarios
# NOTA: Sólo tenemos en cuenta la negación porque es el único operador unario implementado. Si agregamos más, habría que considerarlos acá.

# Instrucciones con efecto
REGEX_EFECTO = re.compile(r'\b(ifnot|if|push|pop|jmp|label)\b')
# \b es un caracter especial de "límite de palabra": el lugar donde una palabra comienza o termina

# x = x + 1   o  x = x - 1  (considera 1 ó 1.0) -> Detecta incrementos/decrementos en forma normalizada
REGEX_INCREMENTO = re.compile(fr'^({ID})\s*=\s*\\1\s*([+\-])\s*(?:1(?:\.0)?)\s*$')
# Grupos: (destino, operador)
# (?:...) indica un "grupo de no captura" (sirve para tratar todo lo que está dentro como una unidad, pero sin extraerla y guardarla en memoria).
# \1 es una "retroreferencia", quiere decir "lo mismo que en el grupo 1" (en este caso: {ID}). La segunda barra (\\1) es para que el motor de re reciba correctamente el caracter.

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

# x = t0 o x = y -> Propagación de copia
REGEX_ASIGNACION_SIMPLE = re.compile(fr'^({ID})\s*=\s*({ID})$')
# Grupos = (destino, origen)
# Grupos = ({ID}, {ID}), lo demás se descarta

# t2 = t1 * c   o   x = a + b -> Propagación en asignaciones binarias que pueden contener IDs o NUM
REGEX_ASIGNACION_BINARIA = re.compile(fr'^({ID})\s*=\s*({ID}|{NUM})\s*({OP_BIN})\s*({ID}|{NUM})$')
# Grupos = (destino, op1, operador, op2)
# Grupos = ({ID} , {ID}|{NUM} , {OP_BIN} , {ID}|{NUM})

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
            hubo_plegado = self.plegado_constantes()
            hubo_propagacion = self.propagacion_copia()
            hubo_eliminacion = self.eliminacion_codigo_muerto()

            if not (hubo_plegado or hubo_propagacion or hubo_eliminacion): # Si no se hicieron cambios, terminamos
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
                            # Diferenciamos entre división entera y decimal según el formato de los operandos
                            if op1.isdigit() and op2.isdigit(): # Si ambos operandos son enteros, hacemos división entera
                                resultado = val1 // val2
                            else: # Si alguno de los operandos es decimal, hacemos división normal
                                resultado = val1 / val2
                        else:
                            raise ZeroDivisionError("División por cero")
                    elif operador == '%':
                        if val2 != 0:
                            # El operador módulo sólo tiene sentido para enteros, así que verificamos que ambos operandos sean enteros antes de aplicarlo
                            if op1.isdigit() and op2.isdigit():
                                resultado = val1 % val2
                            else:
                                raise ValueError("Operador módulo solo válido para enteros")
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
                    else: # Operador no contemplado: no plegamos esta línea
                        nuevo_codigo.append(linea)
                        continue
                    
                    if isinstance(resultado, float) and resultado.is_integer(): # is_integer() sólo funciona para floats, por eso chequeamos el tipo antes
                        resultado = int(resultado) # Para evitar resultados como 5.0
                    
                    nueva_linea = f"{destino} = {resultado}"
                    if nueva_linea != linea:
                        print(f"Plegado de constantes: '{linea}' -> '{nueva_linea}'")
                        hubo_cambios = True
                    nuevo_codigo.append(nueva_linea)
                    continue
        
                except (ZeroDivisionError, ValueError) as e: # Especifico estos tipos de excepciones por las moscas, así evitamos que se cuelen otros errores no contemplados
                    nuevo_codigo.append(linea) # Si hay algún error (ej: división por cero), no optimizamos esta línea
                    print(f"ERROR: {e}. No se puede optimizar la línea '{linea}'")
                    continue 

            # --- Unaria constante (t0 = !5) ---
            match = REGEX_UNARIA_CONSTANTE.match(linea)
            if match:
                destino, operador, operando = match.groups()
                val = float(operando)

                resultado = 0 if val != 0 else 1
                nueva_linea = f"{destino} = {resultado}"
                if nueva_linea != linea:
                    print(f"Plegado de constantes: '{linea}' -> '{nueva_linea}'")
                    hubo_cambios = True
                nuevo_codigo.append(nueva_linea)
                continue

            # --- No hubo match de ningún tipo de plegado ---
            nuevo_codigo.append(linea) # Mantenemos la línea original

        # ----- Fin de la etapa ----- 
        self.codigo = nuevo_codigo # Actualizamos el código con el que trabaja el optimizador, para que las siguientes optimizaciones trabajen sobre el resultado de esta
        return hubo_cambios

    # ---------------- Propagación de copia ----------------
    # Si a una variable se le asigna un valor constante, se sustituyen las apariciones posteriores de ella por el valor correspondiente, siempre que no cambie en el camino
    # Ej: a = 10 
    #     b = a + 5 -> b = 10 + 5
    def propagacion_copia(self):
        """
        Propagación lineal adelante:
        - Propaga constantes: dest = NUM
        - Propaga copias simples: dest = src  
        - Propaga copias complejas: dest = op1 op op2  tratando de sustituir op1/op2 por lo que haya en mapa
        - NO propaga a través de efectos (call/push/pop/jmp/ifnot/label): al encontrarlos se invalida el mapa.
        - NO propaga resultados que provengan de post-incremento (detectamos t = v seguido de v = v + 1).
        - No hace análisis de flujo; sólo recorrido lineal.
        Retorna True si hubieron cambios.
        """
        nuevo_codigo = []
        hubo_cambios = False
        constantes = {} # Guardamos pares (var, cte)
        bloqueados = set() # Conjunto sin duplicados de identificadores con propagación bloqueada

        for linea in self.codigo: 
            
            # Filtro de instrucciones con efecto (saltamos)
            if REGEX_EFECTO.search(linea):
                constantes.clear()
                bloqueados.clear()
                nuevo_codigo.append(linea)
                continue

            # Filtro de incremento tipo i++ (saltamos)
            # Se evalúa primero por ser el caso más específico
            if match := REGEX_INCREMENTO.match(linea):
                var_incrementada = match.group(1)
                # Como var_incrementada cambia, tenemos que invalidar cualquier entrada en el diccionario que dependa de var_incrementada
                limpiar_diccionario(constantes, var_incrementada)
                # Si la línea anterior fue "t = var_incrementada", tenemos que bloquear 't' para no propagar un error
                if nuevo_codigo:
                    if m_previo := REGEX_ASIGNACION_SIMPLE.match(nuevo_codigo[-1]):
                        destino_prev, origen_prev = m_previo.groups()
                        if origen_prev == var_incrementada and destino_prev.startswith('t'):
                            bloqueados.add(destino_prev)
                    nuevo_codigo.append(linea)
                    continue

            # Asignación de constante (ID = NUM)
            if match := REGEX_ASIGNACION_CONSTANTE.match(linea):
                variable, valor = match.groups()
                limpiar_diccionario(constantes,variable)
                constantes[variable] = valor
                nuevo_codigo.append(linea)
                continue

            # Asignación simple (ID = ID)
            if match := REGEX_ASIGNACION_SIMPLE.match(linea):
                destino, origen = match.groups()
                limpiar_diccionario(constantes, destino)
                
                # Peephole: la instrucción anterior define el origen de la actual
                if nuevo_codigo:
                    linea_previa = nuevo_codigo[-1]
                    if m_previo := re.match(fr'^{re.escape(origen)}\s*=\s*(.*)$', linea_previa):
                        expresion_previa = m_previo.group(1) # Extraemos el "op1 operando op 2" de var = op1 operando op2
                        nueva_linea = f"{destino} = {expresion_previa}"
                        nuevo_codigo.append(nueva_linea)

                        print(f"Propagación: {linea_previa} + {linea} -> {nueva_linea}")
                        hubo_cambios = True
                        continue
                
                # Propagación de copia normal
                if origen in constantes and origen not in bloqueados:
                    nueva_linea = f"{destino} = {constantes[origen]}"
                    print(f"Propagación: {linea} -> {nueva_linea}")
                    nuevo_codigo.append(nueva_linea)
                    hubo_cambios = True
                    continue

                nuevo_codigo.append(linea)
                continue

            # Asignación binaria (ID = op1 operador op2)
            if match := REGEX_ASIGNACION_BINARIA.match(linea):
                destino, op1, operador, op2 = match.groups()
                limpiar_diccionario(constantes, destino)

                # Tenemos que sustituir los operando si están en el mapa y NO están bloqueados
                # Operando 1
                if op1 in constantes and op1 not in bloqueados:
                    op1_cambiado = constantes[op1]
                else:
                    op1_cambiado = op1
                # Operando 2
                if op2 in constantes and op2 not in bloqueados:
                    op2_cambiado = constantes[op2]
                else:
                    op2_cambiado = op2

                nueva_linea = f"{destino} = {op1_cambiado} {operador} {op2_cambiado}"
                if nueva_linea != linea:
                    hubo_cambios = True
                    print(f"Propagación: {linea} -> {nueva_linea}")
                nuevo_codigo.append(nueva_linea)
                continue
            
            # No es nada de lo anterior (poco probable, pero por las moscas)
            nuevo_codigo.append(linea)

        self.codigo = nuevo_codigo
        return hubo_cambios

    # ---------------- Eliminación de código muerto ----------------
    # Se eliminan instrucciones que no afectan el resultado del programa, como asignaciones a variables que nunca se usan
    def eliminacion_codigo_muerto(self):
        pass

# ###########################################################################
# Utilidades
# ###########################################################################

def limpiar_diccionario(mapa, clave_eliminada):
    """Recibe un mapa y una clave. Elimina dicha clave y todas las demás cuyo valor dependa de la clave eliminada."""

    if clave_eliminada in mapa:
        del mapa[clave_eliminada]

    claves_a_borrar = [k for k,v in mapa.items() if re.search(fr'\b{re.escape(clave_eliminada)}\b', v)] # re.escape() sirve para neutralizar los caracteres especiales y hacer que la regex los busque como texto literal
    for k in claves_a_borrar:
        del mapa[k]