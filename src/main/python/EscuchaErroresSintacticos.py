from antlr4.error.ErrorListener import ErrorListener
from Enumeraciones import TipoError

class EscuchaErroresSintacticos(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errores = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        
        texto = offendingSymbol.text if offendingSymbol is not None else ""
        mensaje = ""

        # Error parentesis de cierre
        if ("expecting ')'" in msg or "missing ')'" in msg or "no viable alternative at input" in msg) \
           and texto in ["{", ";", "else", "ID", "NUMERO"]:
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un paréntesis de cierre ')' antes de '{texto}' (línea {line})"

        # Error parentesis abierto
        elif ("extraneous input" in msg and texto == ")") or ("missing '('" in msg):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un paréntesis de apertura '(' (línea {line})"

        # Error punto y coma
        elif "expecting ';'" in msg or ("mismatched input" in msg and texto in ["}", "else"]):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un punto y coma ';' al final de la instrucción (línea {line})"

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
