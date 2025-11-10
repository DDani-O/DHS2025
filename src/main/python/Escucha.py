from compiladorParser import compiladorParser
from compiladorListener import compiladorListener
from tablaDeSimbolos.SymbolTable import TS
from tablaDeSimbolos.Variable import Variable
from tablaDeSimbolos.Funcion import Funcion
from Enumeraciones import TipoError
from antlr4 import ErrorNode


class Escucha(compiladorListener):
    def __init__(self):
        super().__init__()
        self.TS = TS.getTS()
        self.huboErrores = False
        # bandera que indica que estamos procesando una declaracion
        # para evitar reportar usos sin inicializar durante su propio parsing
        self.leyendoDeclaracion = False

    # ------------------------------
    # Utilidades
    # ------------------------------
    def registrarError(self, tipo: TipoError, msj: str):
        # mantenemos la salida estilo CODIGOMAL
        self.huboErrores = True
        # imprime con la etiqueta semántica como antes
        print(f"ERROR SEMANTICO: {msj}")

    # ------------------------------
    # Inicio / fin
    # ------------------------------
    def enterPrograma(self, ctx: compiladorParser.ProgramaContext):
        with open("ContenidoTS.txt", "w") as f:
            pass
        print(" ------ Comienza el parsing ------ ")

    def exitPrograma(self, ctx: compiladorParser.ProgramaContext):
        # Al terminar, revisar variables no usadas
        self.buscarVariablesNoUsadas()

        if self.huboErrores:
            with open("ContenidoTS.txt", "w") as f:
                f.write("Imposible generar la TS: Se encontraron errores durante el parsing.\n")
        else:
            # imprimir tabla si no hubo errores
            self.TS.imprimirTS()
        print(" ------ Termina el parsing ------ ")

    # ------------------------------
    # Contextos (bloques y for)
    # ------------------------------
    def enterBloque(self, ctx):
        self.TS.addContexto()

    def exitBloque(self, ctx):
        self.TS.delContexto()

    def enterIfor(self, ctx):
        self.TS.addContexto()

    def exitIfor(self, ctx):
        self.TS.delContexto()

    # ------------------------------
    # Declaraciones
    # ------------------------------
    def enterDeclaracion(self, ctx: compiladorParser.DeclaracionContext):
        # activamos la bandera para no considerar como uso sin inicializar
        # las referencias que formen parte de los inicializadores en la misma linea
        self.leyendoDeclaracion = True

    def exitDeclaracion(self, ctx: compiladorParser.DeclaracionContext):
        # si hubo error de parseo en descendencia, salimos
        if any(isinstance(h, ErrorNode) for h in ctx.getChildren()):
            self.leyendoDeclaracion = False
            return

        # extraer tipo y lista textual (similar a CODIGOMAL original)
        tipo = ctx.expDEC().tipo().getText()
        raw = ctx.expDEC().getText()
        rest = raw[len(tipo):].strip()
        parts = [p.strip() for p in rest.split(',') if p.strip()]

        # recolectar variables en orden izquierdo->derecho
        vars_list = []  # tuplas: (nombre, tiene_inic, inic_text_or_ctx)
        for part in parts:
            if '=' in part:
                nombre, valor = [t.strip() for t in part.split('=', 1)]
                vars_list.append((nombre, True, valor))
            else:
                vars_list.append((part, False, None))

        # primero: agregar todas las variables al contexto en orden
        nuevas = []
        for nombre, tiene_inic, inic in vars_list:
            if self.TS.buscarSimboloContexto(nombre):
                self.registrarError(TipoError.SEMANTICO, f"'{nombre}' ya existe en el contexto.")
                continue
            nueva = Variable(nombre, tipo)
            # NO marcar inicializada aun; se hará despues de validar el inicializador
            self.TS.addSimbolo(nueva)
            nuevas.append((nueva, tiene_inic, inic))


        self.leyendoDeclaracion = False
        for var, tiene_inic, inic in nuevas:
            if tiene_inic and inic is not None:
                tipo_val = self._tipoExpFromTextOrCtx(inic)
                tipo_dest = var.getTipoDato()
                if tipo_val and not self._compatible(tipo_dest, tipo_val):
                    self.registrarError(TipoError.SEMANTICO,
                                        f"Tipo incompatible en inicializador de '{var.getNombre()}': se esperaba '{tipo_dest}', se obtuvo '{tipo_val}'.")
                else:
                    var.setInicializado()

    def enterInitialize(self, ctx: compiladorParser.InitializeContext):
        
        self.leyendoDeclaracion = True

    def exitInitialize(self, ctx: compiladorParser.InitializeContext):
        if ctx.expDEC() is None:
            self.leyendoDeclaracion = False
            return
        if any(isinstance(h, ErrorNode) for h in ctx.getChildren()):
            self.leyendoDeclaracion = False
            return

        expdec = ctx.expDEC()
        tipo = expdec.tipo().getText()
        raw = expdec.getText()
        rest = raw[len(tipo):].strip()
        parts = [p.strip() for p in rest.split(',') if p.strip()]

        vars_list = []
        for part in parts:
            if '=' in part:
                nombre, valor = [t.strip() for t in part.split('=', 1)]
                vars_list.append((nombre, True, valor))
            else:
                vars_list.append((part, False, None))

        # agregar todos y despues evaluar inicializadores como en exitDeclaracion
        nuevas = []
        for nombre, tiene_inic, inic in vars_list:
            if self.TS.buscarSimboloContexto(nombre):
                self.registrarError(TipoError.SEMANTICO, f"'{nombre}' ya existe en el contexto.")
                continue
            nueva = Variable(nombre, tipo)
            self.TS.addSimbolo(nueva)
            nuevas.append((nueva, tiene_inic, inic))

        
        self.leyendoDeclaracion = False
        for var, tiene_inic, inic in nuevas:
            if tiene_inic and inic is not None:
                tipo_val = self._tipoExpFromTextOrCtx(inic)
                tipo_dest = var.getTipoDato()
                if tipo_val and not self._compatible(tipo_dest, tipo_val):
                    self.registrarError(TipoError.SEMANTICO,
                                        f"Tipo incompatible en inicializador de '{var.getNombre()}': se esperaba '{tipo_dest}', se obtuvo '{tipo_val}'.")
                else:
                    var.setInicializado()

    # ------------------------------
    # Asignaciones fuera de declaracion
    # ------------------------------
    def exitExpASIG(self, ctx: compiladorParser.ExpASIGContext):
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        nombre = ctx.ID().getText()

        # Si estamos dentro de una declaracion manejada arriba, no usar este path
        simbolo = self.TS.buscarSimbolo(nombre)
        if simbolo is None:
            self.registrarError(TipoError.SEMANTICO, f"Uso de identificador no declarado '{nombre}'.")
            return

        tipo_dest = simbolo.getTipoDato()
        tipo_val = self.tipoExp(ctx.opal())

        if tipo_val and not self._compatible(tipo_dest, tipo_val):
            self.registrarError(TipoError.SEMANTICO,
                                f"Tipo incompatible en asignación a '{nombre}': se esperaba '{tipo_dest}', pero se obtuvo '{tipo_val}'.")
            return

        simbolo.setInicializado()

        # Evaluar opal para marcar usos internos (si los hay)
        try:
            self.eval_opal(ctx.opal())
        except Exception:
            pass

    # ------------------------------
    # Uso de IDs en expresiones
    # ------------------------------
    def exitFactorCore(self, ctx: compiladorParser.FactorCoreContext):
        if any(isinstance(hijo, ErrorNode) for hijo in ctx.getChildren()):
            return

        if getattr(ctx, 'ID', None) and ctx.ID():
            nombre = ctx.ID().getText()
            simbolo = self.TS.buscarSimbolo(nombre)
            # Si estamos dentro de una declaración múltiple y todavía no se agregó
            # el símbolo, NO reportamos 'no declarado' ahora, se valida luego.
            if simbolo is None:
                if self.leyendoDeclaracion:
                    return
                else:
                    self.registrarError(TipoError.SEMANTICO, f"Uso de identificador no declarado '{nombre}'.")
                    return
            # marcar usado
            simbolo.setUsado()
            # si no esta inicializada y NO estamos analizando inicializadores de su propia declaracion
            if not simbolo.getInicializado() and not self.leyendoDeclaracion:
                self.registrarError(TipoError.SEMANTICO, f"Variable '{nombre}' usada sin inicializar.")

    # ------------------------------
    # Tipos en expresiones
    # ------------------------------
    def tipoExp(self, ctx):
        if ctx is None:
            return None

        # casos hoja
        if getattr(ctx, 'NUMERO', None) and ctx.NUMERO():
            return 'int'

        if getattr(ctx, 'ID', None) and ctx.ID():
            nombre = ctx.ID().getText()
            simbolo = self.TS.buscarSimbolo(nombre)
            # Mismo comportamiento defensivo: si estamos dentro de una declaración,
            # y el símbolo aún no existe, no reportamos 'no declarado' aquí.
            if simbolo is None:
                return None
            simbolo.setUsado()
            if not simbolo.getInicializado() and not self.leyendoDeclaracion:
                self.registrarError(TipoError.SEMANTICO, f"Variable '{nombre}' usada sin inicializar.")
            return simbolo.getTipoDato()

        # recursivo: combinar hijos
        tipos = set()
        for i in range(ctx.getChildCount()):
            try:
                t = self.tipoExp(ctx.getChild(i))
            except Exception:
                t = None
            if t:
                tipos.add(t)

        if len(tipos) == 1:
            return tipos.pop()
        elif len(tipos) > 1:
            # permitir int + double -> double
            if tipos == {'int', 'double'}:
                return 'double'
            self.registrarError(TipoError.SEMANTICO, "Tipos incompatibles en la expresión.")
            return None
        else:
            return None

    def _tipoExpFromTextOrCtx(self, inic):
        # si nos pasan un ctx (ANTLR node) tratamos como antes
        # detectamos si 'inic' tiene atributos parecidos a ctx
        try:
            if hasattr(inic, 'getText') and hasattr(inic, 'getChildCount'):
                return self.tipoExp(inic)
        except Exception:
            pass

        # si es string, analizamos
        if isinstance(inic, str):
            txt = inic
            # numero con punto -> double
            if txt.replace('.', '', 1).isdigit():
                return 'double' if '.' in txt else 'int'
            # si es un identificador simple, buscar simbolo
            simbolo = self.TS.buscarSimbolo(txt)
            if simbolo:
                simbolo.setUsado()
                if not simbolo.getInicializado() and not self.leyendoDeclaracion:
                    self.registrarError(TipoError.SEMANTICO, f"Variable '{txt}' usada sin inicializar.")
                return simbolo.getTipoDato()
        return None

    # ------------------------------
    # Reglas de compatibilidad de tipos
    # ------------------------------
    def _compatible(self, tipo_dest, tipo_val):
        # igual es compatible
        if tipo_dest == tipo_val:
            return True
        # promoción int -> double permitida
        if tipo_dest == 'double' and tipo_val == 'int':
            return True
        # sino incompatible
        return False

    # ------------------------------
    # Evaluación liviana para valores constantes
    # ------------------------------
    def eval_opal(self, ctx):
        try:
            if getattr(ctx, 'NUMERO', None) and ctx.NUMERO():
                return int(ctx.NUMERO().getText())

            if getattr(ctx, 'ID', None) and ctx.ID():
                return None

            import re
            text = ctx.getText()
            if re.fullmatch(r"[0-9+\-*/%()\.\s]+", text):
                return eval(text)
            return None
        except Exception:
            return None

    # ------------------------------
    # Variables no usadas
    # ------------------------------
    def buscarVariablesNoUsadas(self):
        # si el TS tiene historial de contextos, lo usamos (igual que CODIGOMAL)
        if not hasattr(self.TS, 'historialCTX'):
            return
        for contexto in self.TS.historialCTX:
            for nombre, simbolo in list(contexto.simbolos.items()):
                if not simbolo.getUsado():
                    self.registrarError(TipoError.SEMANTICO, f"Variable '{nombre}' declarada pero no utilizada.")

    def buscarExistenciaVariable(self, nombre):
        simbolo = self.TS.buscarSimbolo(nombre)
        if simbolo is None:
            self.registrarError(TipoError.SEMANTICO, f"Uso de identificador no declarado '{nombre}'.")
            return None
        return simbolo

    def __str__(self):
        return "Escucha (fase semántica)"