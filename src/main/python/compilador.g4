grammar compilador;

fragment LETRA : [A-Za-z] ;
fragment DIGITO : [0-9] ;


// ======= Definición de símbolos =======
PA : '(' ;
PC : ')' ;
LLA : '{' ;
LLC : '}' ;
PYC : ';' ;

IGUAL    : '==' ;
DISTINTO :'!=' ;
MAYOR    : '>' ;
MENOR    : '<' ;
MAYORIG  : '>=' ;
MENORIG  : '<=' ;
AND      : '&&' ;
OR       : '||' ;
NOT      : '!' ;

ASIG : '=' ;
COMA : ',' ;
SUMA : '+' ;
INC : '++' ;
RESTA : '-' ;
DEC : '--' ;
MULT : '*' ;
DIV : '/' ;
MOD : '%' ;

NUMERO : DIGITO+ ;

// Palabras reservadas
INT : 'int' ;
DOUBLE : 'double' ;
CHAR : 'char' ;
VOID : 'void' ;

IF :    'if' ;
ELSE :  'else' ;
FOR :   'for' ;
WHILE : 'while' ;

RETURN : 'return' ;

ID : (LETRA | '_')(LETRA | DIGITO | '_')* ;

WS : [ \n\r\t] -> skip ;
OTRO : . ;

// s : ID     {print("ID ->" + $ID.text + "<--") }         s
//   | NUMERO {print("NUMERO ->" + $NUMERO.text + "<--") } s
//   | OTRO   {print("Otro ->" + $OTRO.text + "<--") }     s
//   | EOF
//   ;

// s : PA s PC s
//   |
//   ;

// ======= Estructura básica =======

programa : instrucciones EOF ;

instrucciones : instruccion instrucciones
              |
              ;

instruccion : asignacion
            | declaracion
            | iif
            | iwhile
            | ifor
            | bloque
            | prototipo
            | funcion
            | ireturn
            | llamadaFunc PYC
            ;

bloque : LLA instrucciones LLC ;

// ======= Funciones =======

// Prototipado
prototipo : tipo ID PA listParamsProt? PC PYC ; // el '?' significa "0 o 1 veces"
listParamsProt : parametroProt (COMA parametroProt)*;
parametroProt : tipo
              | tipo ID // en los prototipos, el nombre es opcional
              ;

// Definición
funcion : tipo ID PA listParamsDef? PC bloque ;
listParamsDef : parametroDef (COMA parametroDef)* ;
parametroDef : tipo ID; // en una definición, el nombre es obligatorio

ireturn : RETURN opal PYC 
        | RETURN PYC
        ;

// Llamada
llamadaFunc : ID PA listArgs? PC ;
listArgs : opal (COMA opal)* ; // las llamadas a funciones están presentes como factores en las operaciones

// ======= Instrucciones de control =======

iwhile : WHILE PA opal PC instruccion ;

iif : IF PA opal PC instruccion ielse ;
ielse : ELSE instruccion
      |
      ;

ifor : FOR PA initialize PYC test PYC step PC instruccion 
     | FOR PA initialize PYC test PYC step PC PYC
     ;

// Solo puede ser una lista de todo dec., una lista de todo asig. o vacío
initialize : expDEC
           | expASIG (COMA expASIG)*
           |
           ;

// Condición a probar. Puede ser una expresión o estar vacía
test : opal
     |
     ;

// Lista de expresiones separadas por coma o vacío
step: exp listStep
     |
     ;
listStep : COMA step
         |
         ;

// ======= Declaraciones y asignación de variables =======

declaracion : expDEC PYC ;
expDEC: tipo ID inic listavar ;
tipo : INT
     | DOUBLE
     | CHAR
     | VOID
     ;

listavar : COMA ID inic listavar 
         |
         ;

inic : ASIG opal 
     |
     ;

asignacion : expASIG PYC ;
expASIG : ID ASIG opal ;

// ======= Operaciones aritmeticológicas =======

opal : expOR ; // Toda operación tiene implícita una operación OR
/* 
El orden de precedencia organiza de "lo más chico" a "lo más grande".
Incluso cuando en realidad son operaciones "diferentes", el hecho de
resolver primero una y después la otra, implica que la segunda "contiene"
a la primera.
Como resolvemos todo mediante recursividad, tenemos que organizar las
operaciones en orden inverso (declarar PRIMERO "lo más grande" y, a la
hora de leer, "ENTRAR" por "lo más grande" y ver cómo está formado).
*/

// Operaciones lógicas
expOR : expAND o; // Toda operación OR puede contener varias operaciones AND
o : OR expAND o
  |
  ;

expAND: expIGUALDAD a; // Las operaciones AND pueden necesitar resolver alguna operación de igualdad
a : AND expIGUALDAD a
  |
  ;

expIGUALDAD: expCOMP i; // Las igualdades pueden necesitar resolver alguna comparación primero
i : IGUAL expCOMP i
  | DISTINTO expCOMP i
  |
  ;

expCOMP: exp c; // Las comparaciones pueden necesitar resolver alguna expresión aritmética primero
c : MAYOR exp c
  | MAYORIG exp c
  | MENOR exp c
  | MENORIG exp c
  |
  ;

// Operaciones aritméticas
exp : term e ; // Las expresiones aritméticas están formadas por uno o más términos
e : SUMA term e
  | RESTA term e
  |
  ;

term : factor t ; // Los términos están formados por uno o más factores
t : MULT factor t
  | DIV factor t
  | MOD factor t
  |
  ;

factor : (NOT | INC | DEC)? factorSufix; 
factorSufix : factorCore (INC | DEC)? ;
factorCore : NUMERO
           | ID
           | PA exp PC
           | llamadaFunc
           ;