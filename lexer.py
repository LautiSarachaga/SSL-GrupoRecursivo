import ply.lex as lex
import os
import sys
import datetime

# ==================================================
# TOKENS
# ==================================================

tokens = (

    # IDENTIFICADORES
    "IDENT",
    # LITERALES
    "NUMBER",
    "TEMP",
    "PERCENT",
    "TIME",
    "STRING",
    # TIPOS ESPECIALES
    "BOOL",
    "MODO",
    "COLOR",
    # OPERADORES
    "ASSIGN",
    "EQ",
    "NEQ",
    "GT",
    "LT",
    "GTE",
    "LTE",

    # SIMBOLOS
    "DOT",
    "LPAREN",
    "RPAREN",

    # OTROS
    "NEWLINE",
)

# ==================================================
# KEYWORDS
# ==================================================

keywords = {
    "WHEN": "WHEN",
    "THEN": "THEN",
    "ELSE": "ELSE",
    "END": "END",
    "AND": "AND",
    "OR": "OR",
    "NOT": "NOT",
    "DO": "DO",
    "IF": "IF",
    "EVERY": "EVERY"
}

tokens = tokens + tuple(keywords.values())

# ==================================================
# BOOLS / MODOS / COLORES
# ==================================================

bools = ["ON", "OFF", "TRUE", "FALSE"]

modos = ["FRIO", "CALOR", "VENT"]

colores = ["RED", "GREEN", "BLUE", "WHITE", "YELLOW"]

# ==================================================
# IGNORAR ESPACIOS
# ==================================================

t_ignore = " \t"

# ==================================================
# OPERADORES
# ==================================================

t_EQ      = r'=='
t_NEQ     = r'!='
t_GTE     = r'>='
t_LTE     = r'<='
t_GT      = r'>'
t_LT      = r'<'

t_ASSIGN  = r'='

# ==================================================
# SIMBOLOS
# ==================================================

t_DOT     = r'\.'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

# ==================================================
# COMENTARIOS
# ==================================================

def t_COMMENT(t):
    r'//.*'
    pass

# ==================================================
# NEWLINE
# ==================================================

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

# ==================================================
# TEMPERATURA
# ==================================================

def t_TEMP(t):
    r'\d+(\.\d+)?°C'
    return t

# ==================================================
# PORCENTAJE
# ==================================================

def t_PERCENT(t):
    r'\d+(\.\d+)?%'
    return t

# ==================================================
# HORA
# ==================================================

def t_TIME(t):
    r'\d{1,2}:\d{2}'
    return t

# ==================================================
# STRING
# ==================================================

def t_STRING(t):
    r'"([^\\\n]|(\\.))*?"'
    t.value = t.value[1:-1]
    return t

# ==================================================
# NUMBER
# ==================================================

def t_NUMBER(t):
    r'\d+(\.\d+)?'
    return t

# ==================================================
# IDENTIFICADORES
# ==================================================

def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z0-9_@.-]*'

    mayus = t.value.upper()

    # KEYWORDS

    if mayus in keywords:
        t.type = keywords[mayus]
        t.value = mayus
        return t

    # BOOLS

    if mayus in bools:
        t.type = "BOOL"
        t.value = mayus
        return t

    # MODOS

    if mayus in modos:
        t.type = "MODO"
        t.value = mayus
        return t

    # COLORES

    if mayus in colores:
        t.type = "COLOR"
        t.value = mayus
        return t

    return t

# ==================================================
# ERROR
# ==================================================

def t_error(t):

    print(
        f"Carácter inválido '{t.value[0]}' "
        f"en línea {t.lineno}"
    )

    t.lexer.skip(1)

# ==================================================
# BUILD
# ==================================================

lexer = lex.lex()

# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    with open("entrada.txt", "r", encoding="utf-8") as f:
        data = f.read()

    lexer.input(data)

    print("\n=== TOKENS ===\n")

    while True:

        tok = lexer.token()

        if not tok:
            break

        print(
            f"Tipo: {tok.type:<10} Valor: {repr(tok.value)}"
        )