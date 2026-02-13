from compiladorVisitor import compiladorVisitor
from compiladorParser import compiladorParser

class Caminante (compiladorVisitor) :
    def __init__(self):
        super().__init__()
        self.codigoIntermedio = [] # Buffer de salida para el código intermedio generado
        self.tempCounter = 0 # Contador para generar nombres de variables temporales
        self.labelCounter = 0 # Contador para generar nombres de etiquetas 

    # ###########################################################################
    # Utilidades
    # ###########################################################################

    def generarTemporal(self):
        """Retorna en formato de str un nombre tipo 'tX' para una variable temporal, donde X es un número incremental."""
        self.tempCounter += 1
        return f"t{self.tempCounter}"
    def generarEtiqueta(self):
        """Retorna en formato de str un nombre tipo 'LX' para una etiqueta, donde X es un número incremental."""
        self.labelCounter += 1
        return f"L{self.labelCounter}"
    
    # ###########################################################################
    # Recorrido del árbol (no ocurre por default)
    # ###########################################################################

    def visitPrograma (self, ctx:compiladorParser.ProgramaContext):
        self.visitChildren(ctx)

    def visitInstrucciones(self, ctx):
        self.visitChildren(ctx)

    def visitInstruccion(self, ctx):
        # Instrucción genérica

        # Instrucciones específicas manejadas en sus propios métodos
        self.visitChildren(ctx)

    def visitBloque(self, ctx):
        self.visitChildren(ctx)

    # ###########################################################################
    # Generador del código intermedio
    # ###########################################################################
    
    # ------------------ Traducción de asignaciones ------------------

    def visitAsignacion(self, ctx):
        self.visit(ctx.expASIG())

    def visitExpASIG(self, ctx):
        # expASIG : ID ASIG opal ;
        destino = ctx.ID().getText()
        valor = self.visit(ctx.opal())
        self.codigoIntermedio.append(f"{destino} = {valor}")
    
    def visitOpal(self, ctx):
        return self.visit(ctx.expOR()) # Propagación del resultado

    def visitExpOR(self, ctx):
        left = self.visit(ctx.expAND()) # Resolvemos el lado izquierdo, generando las instrucciones pertinentes en el proceso
        return self._resolverOR(left, ctx.o()) # Delegamos la resolución del resto de la expresión a un método auxiliar para manejar la recursión de manera más limpia
    def _resolverOR(self, left, octx):
        if octx is None or octx.getChildCount() == 0: # Caso base: no hay más operadores OR, retornamos lo que teníamos
            return left

        right = self.visit(octx.expAND()) # Resolvemos el lado derecho del operador OR actual (generando las instrucciones pertinentes en el proceso también)
        temp = self.generarTemporal()
        self.codigoIntermedio.append(f"{temp} = {left} || {right}") # Generamos una instrucción para el operador OR actual (C es left-associative)

        return self._resolverOR(temp, octx.o()) # Recursión: el resultado de la operación que acabamos de resolver se convierte en el "lado izquierdo" para resolver el siguiente operador OR (si es que hay más), siguiendo el patrón left-associative
    
    # NOTA: El patrón se repite para casi todos los niveles de precedencia (la lógica que usamos al definir la precedencia de los operadores es la misma), manejando la recursión de manera similar.

    def visitExpAND(self, ctx):
        left = self.visit(ctx.expIGUALDAD())
        return self._resolverAND(left, ctx.a())
    def _resolverAND(self, left, actx):
        if actx is None or actx.getChildCount() == 0:
            return left

        right = self.visit(actx.expIGUALDAD())
        temp = self.generarTemporal()
        self.codigoIntermedio.append(f"{temp} = {left} && {right}")

        return self._resolverAND(temp, actx.a())

    def visitExpIGUALDAD(self, ctx):
        left = self.visit(ctx.expCOMP())
        return self._resolverIGUALDAD(left, ctx.i())
    def _resolverIGUALDAD(self, left, ictx):
        if ictx is None or ictx.getChildCount() == 0:
            return left

        if ictx.IGUAL():
            op = "=="
        else:
            op = "!="

        right = self.visit(ictx.expCOMP())
        temp = self.generarTemporal()
        self.codigoIntermedio.append(f"{temp} = {left} {op} {right}")

        return self._resolverIGUALDAD(temp, ictx.i())

    def visitExpCOMP(self, ctx):
        left = self.visit(ctx.exp())
        return self._resolverCOMP(left, ctx.c())
    def _resolverCOMP(self, left, cctx):
        if cctx is None or cctx.getChildCount() == 0:
            return left

        if cctx.MAYOR():
            op = ">"
        elif cctx.MAYORIG():
            op = ">="
        elif cctx.MENOR():
            op = "<"
        else:
            op = "<="

        right = self.visit(cctx.exp())
        temp = self.generarTemporal()
        self.codigoIntermedio.append(f"{temp} = {left} {op} {right}")

        return self._resolverCOMP(temp, cctx.c())

    def visitExp(self, ctx):
        left = self.visit(ctx.term())
        return self._resolverSUMA(left, ctx.e())
    def _resolverSUMA(self, left, ectx):
        if ectx is None or ectx.getChildCount() == 0:
            return left

        if ectx.SUMA():
            op = "+"
        else:
            op = "-"

        right = self.visit(ectx.term())
        temp = self.generarTemporal()
        self.codigoIntermedio.append(f"{temp} = {left} {op} {right}")

        return self._resolverSUMA(temp, ectx.e())

    def visitTerm(self, ctx):
        left = self.visit(ctx.factor())
        return self._resolverMULT(left, ctx.t())
    def _resolverMULT(self, left, tctx):
        if tctx is None or tctx.getChildCount() == 0:
            return left

        if tctx.MULT():
            op = "*"
        elif tctx.DIV():
            op = "/"
        else:
            op = "%"

        right = self.visit(tctx.factor())
        temp = self.generarTemporal()
        self.codigoIntermedio.append(f"{temp} = {left} {op} {right}")

        return self._resolverMULT(temp, tctx.t())
    
    # La cosa cambia a partir de este punto (no tenemos un patrón recursivo).
    
    def visitFactor(self, ctx): # Prefijos
        valor = self.visit(ctx.factorSufix())

        if ctx.INC():
            self.codigoIntermedio.append(f"{valor} = {valor} + 1")
            return valor

        if ctx.DEC():
            self.codigoIntermedio.append(f"{valor} = {valor} - 1")
            return valor

        if ctx.NOT():
            temp = self.generarTemporal()
            self.codigoIntermedio.append(f"{temp} = !{valor}")
            return temp

        return valor

    def visitFactorSufix(self, ctx):
        valor = self.visit(ctx.factorCore())

        if ctx.INC():
            temp = self.generarTemporal()
            self.codigoIntermedio.append(f"{temp} = {valor}")
            self.codigoIntermedio.append(f"{valor} = {valor} + 1")
            return temp

        if ctx.DEC():
            temp = self.generarTemporal()
            self.codigoIntermedio.append(f"{temp} = {valor}")
            self.codigoIntermedio.append(f"{valor} = {valor} - 1")
            return temp

        return valor

    def visitFactorCore(self, ctx):
        if ctx.NUMERO():
            return ctx.NUMERO().getText()
        if ctx.CARACTER():
            return ctx.CARACTER().getText()
        if ctx.ID():
            return ctx.ID().getText()
        if ctx.exp():
            return self.visit(ctx.exp())
        # if ctx.llamadaFuncion():
        #     return self.visit(ctx.llamadaFuncion())

    # ------------------ Traducción de declaraciones ------------------
    def visitDeclaracion(self, ctx):
        self.visit(ctx.expDEC())

    def visitExpDEC(self, ctx):
        self.visit(ctx.listaDeclaradores())

    def visitListaDeclaradores(self, ctx):
        for decl in ctx.declarador():
            self.visit(decl)

    def visitDeclarador(self, ctx):
        # declarador : ID inic ;
        # inic : ASIG opal
        #     |
        #     ;
        if ctx.inic().ASIG() is not None: # Si hay una inicialización, generamos el código necesario
            destino = ctx.ID().getText()
            valor = self.visit(ctx.inic().opal())
            self.codigoIntermedio.append(f"{destino} = {valor}")
        # Si no hay inicialización, no es necesario generar código (en C esto sólo reservaría espacio en memoria, pero como no estamos manejando memoria, no es necesario generar ninguna instrucción para una declaración sin inicialización)

    # ------------------ Traducción de bucles y condicionales ------------------

    def visitIif(self, ctx):
        # iif : IF PA opal PC instruccion ielse ;
        # ielse : ELSE instruccion | ;

        finLabel = self.generarEtiqueta() # Etiqueta de fin del if
        tieneElse = False 

        if ctx.ielse().ELSE() is not None: 
            tieneElse = True
            elseLabel = self.generarEtiqueta() # Etiqueta de inicio del else (si es que hay un else)

        condicion = self.visit(ctx.opal()) # Generamos el código para evaluar la condición, cuyo resultado queda guardado en una temporal devuelta por el visit de opal
        self.codigoIntermedio.append(f"ifnot {condicion} jmp {elseLabel if tieneElse else finLabel}") # Si la condición es falsa, saltamos al else (si existe) o al fin del if
        self.visit(ctx.instruccion()) # Generamos el código para el cuerpo del if-true
        if tieneElse:
            self.codigoIntermedio.append(f"jmp {finLabel}") # Saltamos al fin del if después de ejecutar el cuerpo del if-true
            self.codigoIntermedio.append(f"label {elseLabel}:")
            self.visit(ctx.ielse().instruccion()) # Generamos el código para el cuerpo del else
        self.codigoIntermedio.append(f"label {finLabel}:")

    def visitIwhile(self, ctx):
        # iwhile : WHILE PA opal PC instruccion ;
    
        retorno = self.generarEtiqueta() # Etiqueta de retorno al inicio del bucle
        fin = self.generarEtiqueta() # Etiqueta de fin del bucle

        self.codigoIntermedio.append(f"label {retorno}:")
        condicion = self.visit(ctx.opal()) # Generamos el código para evaluar la condición, cuyo resultado queda guardado en una temporal devuelta por el visit de opal
        self.codigoIntermedio.append(f"ifnot {condicion} jmp {fin}")
        self.visit(ctx.instruccion()) # Generamos el código para el cuerpo del bucle
        self.codigoIntermedio.append(f"jmp {retorno}")
        self.codigoIntermedio.append(f"label {fin}:")
    
    def visitIfor(self, ctx):
        # ifor : FOR PA initialize PYC test PYC step PC instruccion 
        #      | FOR PA initialize PYC test PYC step PC PYC
        #      ;
        retorno = self.generarEtiqueta() # Etiqueta de retorno al inicio del bucle
        fin = self.generarEtiqueta() # Etiqueta de fin del bucle

        self.visit(ctx.initialize()) # Generamos el código para la parte de inicialización del for
        self.codigoIntermedio.append(f"label {retorno}:")
        condicion = self.visit(ctx.test()) # Generamos el código para evaluar la condición, cuyo resultado queda guardado en una temporal devuelta por el visit de test
        self.codigoIntermedio.append(f"ifnot {condicion} jmp {fin}")
        if ctx.instruccion() is not None:
            self.visit(ctx.instruccion()) # Generamos el código para el cuerpo del bucle (si es que existe, ya que la regla permite un for sin cuerpo)
        self.visit(ctx.step()) # Generamos el código para el step del for
        self.codigoIntermedio.append(f"jmp {retorno}")
        self.codigoIntermedio.append(f"label {fin}:")

    def visitInitialize(self, ctx):
        if ctx.expDEC(): # Sólo una ocurrencia, por lo que devuelve un nodo
            self.visit(ctx.expDEC())
        if ctx.expASIG(): # Como puede haber múltiples ocurrencias devuelve una lista de nodos
            for e in ctx.expASIG():
                self.visit(e)

    def visitTest(self, ctx):
        if ctx.opal() is not None:
            return self.visit(ctx.opal()) # Generamos el código para evaluar la condición y devuelve su resultado en una temporal
    
    def visitStep(self, ctx):
        if ctx.exp() is None: # Base: expresión vacía
            return
        self.visit(ctx.exp()) # Generamos el código para la expresión actual
        self.visit(ctx.listStep()) # Delegamos el resto del step
    def visitListStep(self, ctx):
        if ctx.step() is None:
            return
        self.visit(ctx.step()) # Recursividad

    # ------------------ Traducción de funciones ------------------

    def visitLlamadaFuncion(self, ctx):
        return super().visitLlamadaFuncion(ctx)

    def visitFuncion(self, ctx):
        return super().visitFuncion(ctx)
    
    def visitReturn(self, ctx):
        return super().visitReturn(ctx)