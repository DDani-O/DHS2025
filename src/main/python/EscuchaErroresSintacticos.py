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
              or ("no viable alternative at input" in msg and texto.isidentifier())
              or (texto == "," and ("no viable alternative" in msg or "extraneous input" in msg)) # Atrapa comas huérfanas o mal ubicadas
              or ("no viable alternative" in msg and any(tipo in msg for tipo in ["'int,'", "'float,'", "'double,'", "'char,'", "'bool,'"])) # Atrapa el caso donde ANTLR junta el tipo y la coma en el mensaje (ej: 'int,')
              or ("missing ','" in msg) # Atrapa casos como "int x y z;" donde faltan las comas intermedias
              or ("extraneous input" in msg and texto.isidentifier())):
            mensaje = f"ERROR {TipoError.SINTACTICO}: formato incorrecto en la lista de declaración de variables (línea {line})"

        # Error llave de cierre
        elif ("expecting '}'" in msg 
              or "missing '}'" in msg 
              or ("no viable alternative at input" in msg and texto == "<EOF>")):
            linea_reportada = line
            # Cuando falta una llave de cierre, ANTLR suele darse cuenta recién al final del archivo (<EOF>).
            # Para mejorar la precisión, podemos apuntar a la última línea de código real en lugar de la línea vacía del EOF.
            if texto == "<EOF>" and offendingSymbol is not None and offendingSymbol.tokenIndex > 0:
                tokens = recognizer.getInputStream().tokens
                prev_token = tokens[offendingSymbol.tokenIndex - 1]
                linea_reportada = prev_token.line
                
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta una llave de cierre '}}' (línea {linea_reportada})"

        # Error llave de apertura
        elif ("expecting '{'" in msg 
              or "missing '{'" in msg 
              or ("mismatched input" in msg and "expecting '{'" in msg)):
            mensaje = f"ERROR {TipoError.SINTACTICO}: falta una llave de apertura '{{' (línea {line})"

        # Otros errores
        else:
            mensaje = f"ERROR {TipoError.SINTACTICO} (línea {line}, columna {column}): {msg}"

        # Print
        self.errores.append(mensaje)
        print(mensaje)