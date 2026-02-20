from antlr4.error.ErrorListener import ErrorListener
from Enumeraciones import TipoError

class EscuchaErroresSintacticos(ErrorListener):
    def __init__(self):
        super().__init__()
        self.errores = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        
        texto = offendingSymbol.text if offendingSymbol is not None else ""
        mensaje = ""

        tokens = recognizer.getInputStream().tokens
        prev_token = tokens[offendingSymbol.tokenIndex - 1] if offendingSymbol and offendingSymbol.tokenIndex > 0 else None

        # Falta identificador antes de la coma
        if ("no viable alternative at input" in msg and texto == "," and prev_token and prev_token.text in ["int", "float", "char", "bool"]):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un identificador antes de la coma en la declaración (línea {line})"
        
        # Se esperaba identificador después del tipo
        elif ("no viable alternative at input" in msg and texto in ["int", "float", "char", "bool"]):
            mensaje = f"ERROR {TipoError.SINTACTICO}: se esperaba un identificador después del tipo '{texto}' (línea {line})"

        # Se esperaba identificador después de la coma
        elif (texto == ";" and prev_token and prev_token.text == ","):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un identificador después de la coma en la declaración (línea {line})"

        # Falta identificador entre comas
        elif ("extraneous input" in msg and texto == "," and prev_token and prev_token.text == ","):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un identificador entre comas en la declaración (línea {line})"
        
        # Falta coma entre identificadores
        elif (texto.isidentifier() and prev_token and prev_token.text.isidentifier() and offendingSymbol.tokenIndex >= 2 and tokens[offendingSymbol.tokenIndex - 2].text in ["int", "float", "char", "bool"]):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta una coma entre identificadores en la declaración (línea {line})"

        # Formato incorrecto en lista de declaración
        elif ("missing ID" in msg 
              or ("mismatched input" in msg and "ID" in msg)):
            mensaje = f"ERROR {TipoError.SINTACTICO}: formato incorrecto en la lista de declaración de variables (línea {line})"

        # Condición vacía
        elif ("mismatched input ')'" in msg and prev_token and prev_token.text == "("):
            mensaje = f"ERROR {TipoError.SINTACTICO}: condición vacía en estructura de control (línea {line})"

        # Operadores consecutivos
        elif (("no viable alternative at input" in msg or "mismatched input" in msg) 
              and texto in ["+", "-", "*", "/", "%", "&&", "||", ">", "<", ">=", "<=", "==", "!="]):
            mensaje = f"ERROR {TipoError.SINTACTICO}: uso inválido de operadores consecutivos (línea {line})"

        # Falta expresión antes del ;
        elif ("mismatched input" in msg and texto == ";"):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta una expresión antes del ';' (línea {line})"

        # Falta paréntesis de cierre
        elif (("expecting ')'" in msg or "missing ')'" in msg) 
              or ("no viable alternative at input" in msg and texto in ["{", ";", "else"])):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un paréntesis de cierre ')' antes de '{texto}' (línea {line})"

        # Falta paréntesis de apertura
        elif (("extraneous input" in msg and texto == ")") 
              or ("missing '('" in msg)):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un paréntesis de apertura '(' (línea {line})"

        # Falta punto y coma
        elif ("expecting ';'" in msg 
                or ("mismatched input" in msg and "expecting ';'" in msg)
                or ("mismatched input" in msg and texto in ["}", "else"])
                or ("no viable alternative at input" in msg and texto in ["int", "double", "if", "while", "for", "return"])):
            linea_reportada = line
            if "expecting ';'" in msg or "no viable alternative" in msg:
                if offendingSymbol and offendingSymbol.tokenIndex > 0:
                    prev_token = tokens[offendingSymbol.tokenIndex - 1]
                    linea_reportada = prev_token.line
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta un punto y coma ';' al final de la instrucción (línea {linea_reportada})"

        # Falta tipo en declaración
        elif ("no viable alternative at input" in msg and texto.isidentifier()):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta el tipo en la declaración de variable (línea {line})"

        # Posible falta de ; o ) antes de }
        elif ("no viable alternative at input" in msg and texto == "}"):
            mensaje = f"ERROR {TipoError.SINTACTICO}: probablemente falta un ';' o ')' antes del bloque '}}' (línea {line})"

        # Otros errores
        else:
            mensaje = f"ERROR {TipoError.SINTACTICO} (línea {line}, columna {column}): {msg}"

        self.errores.append(mensaje)
        print(mensaje)