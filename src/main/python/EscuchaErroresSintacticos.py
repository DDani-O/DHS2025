from antlr4.error.ErrorListener import ErrorListener
from Enumeraciones import TipoError

class EscuchaErroresSintacticos(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errores = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        # El análisis de errores sintácticos que implementamos acá se basa en identificar patrones en los mensajes de error generados por ANTLR.
        
        texto = offendingSymbol.text if offendingSymbol is not None else ""
        mensaje = ""

        # print(f"[DEBUG] msg: {msg}, texto: {texto}") # Debug para ver los mensajes de error que nos tira ANTLR

        # Error parentesis de cierre
        if ("expecting ')'" in msg or "missing ')'" in msg or "no viable alternative at input" in msg) \
           and texto in ["{", ";", "else", "ID", "NUMERO"]:
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un paréntesis de cierre ')' antes de '{texto}' (línea {line})"

        # Error parentesis abierto
        elif ("extraneous input" in msg and texto == ")") or ("missing '('" in msg):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un paréntesis de apertura '(' (línea {line})"

        # Error punto y coma
        elif ("expecting ';'" in msg 
                or ("mismatched input" in msg and "expecting ';'" in msg)
                or ("mismatched input" in msg and texto in ["}", "else"])
                or ("no viable alternative at input" in msg and texto in ["int", "double", "if", "while", "for", "return"])):
            linea_reportada = line # Por defecto, reportamos la línea del token ofensivo
            if "expecting ';'" in msg or "no viable alternative" in msg: # Cuando el mensaje de error tiene alguna de estas descripciones, suele ser que detectó el error en la siguiente línea no vacía.
            # Lo que sigue busca mejorar la precisión de la línea reportada. No es exacto, pero mejora un poco.
                tokens = recognizer.getInputStream().tokens # Cargamos todos los tokens
                if offendingSymbol.tokenIndex > 0:
                    prev_token = tokens[offendingSymbol.tokenIndex - 1]
                    linea_reportada = prev_token.line
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un punto y coma ';' al final de la instrucción (línea {linea_reportada})"

        # Error declaracion de variables
        elif ("missing ID" in msg 
              or ("mismatched input" in msg and "ID" in msg) 
              or ("no viable alternative at input" in msg and texto.isidentifier())):
            mensaje = f"ERROR {TipoError.SINTACTICO}: formato incorrecto en la lista de declaración de variables (línea {line})"

        # Error llave de cierre
        elif "no viable alternative at input" in msg and texto == "}":
            mensaje = f"ERROR {TipoError.SINTACTICO}: probablemente falta un ';' o ')' antes del bloque '}}' (línea {line})"

        # Otros errores
        else:
            mensaje = f"ERROR {TipoError.SINTACTICO} (línea {line}, columna {column}): {msg}"

        # Print
        self.errores.append(mensaje)
        print(mensaje)
