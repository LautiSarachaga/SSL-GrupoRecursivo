import re

# =========================
# TOKEN DEFINITIONS
# =========================

TOKEN_SPECIFICATION = [
    # Comentarios
    ("COMMENT",      r"//.*"),

    # Saltos de línea (IMPORTANTE para el parser)
    ("NEWLINE",      r"\n+"),

    # Espacios (ignorar)
    ("SKIP",         r"[ \t]+"),

    # Palabras reservadas
    ("KEYWORD",      r"\b(WHEN|IF|THEN|ELSE|DO|END|EVERY|AND|OR|NOT)\b"),

    # Booleanos
    ("BOOL",         r"\b(TRUE|FALSE|ON|OFF)\b"),

    # Email
    ("EMAIL",        r"[a-zA-Z0-9._+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,4}(\.[a-zA-Z]{2,4})*"),

    # Fecha
    ("DATE",         r"\b\d{2}/\d{2}/\d{4}\b"),

    # Hora
    ("TIME",         r"\b\d{2}:\d{2}\b"),

    # Temperatura
    ("TEMP",         r"-?\d+(\.\d+)?°C"),

    # Porcentaje
    ("PERCENT",      r"\d+%"),

    # Tiempo
    ("DURATION",     r"\d+[smh]"),

    # Iluminancia
    ("LUX",          r"\d+lux"),

    # Número genérico (NUEVO)
    ("NUMBER",       r"\d+(\.\d+)?"),

    # String (mejorado: soporta " y ')
    ("STRING",       r'"[^"]*"|\'[^\']*\''),
    
    # Operadores
    ("EQ",           r"=="),
    ("NEQ",          r"!="),
    ("GTE",          r">="),
    ("LTE",          r"<="),
    ("GT",           r">"),
    ("LT",           r"<"),
    ("ASSIGN",       r"="),

    # Paréntesis (NUEVO)
    ("LPAREN",       r"\("),
    ("RPAREN",       r"\)"),

    # Punto
    ("DOT",          r"\."),

    # Valores específicos
    ("COLOR",        r"\b(RED|GREEN|BLUE|WHITE|YELLOW)\b"),
    ("MODO",         r"\b(FRIO|CALOR|VENT)\b"),

    # Identificadores
    ("IDENT",        r"[a-zA-Z_][a-zA-Z0-9_]*"),

    # Error
    ("MISMATCH",     r"."),
]

# Compilar regex
TOK_REGEX = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPECIFICATION)
MASTER_REGEX = re.compile(TOK_REGEX, re.IGNORECASE)


# =========================
# TOKEN CLASS
# =========================

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"{self.type}({self.value}) at {self.line}:{self.column}"


# =========================
# LEXER
# =========================

def lexer(code):
    tokens = []
    line_num = 1
    line_start = 0

    for match in MASTER_REGEX.finditer(code):
        kind = match.lastgroup
        value = match.group()
        column = match.start() - line_start

        # Manejo de saltos de línea
        if kind == "NEWLINE":
            tokens.append(Token("NEWLINE", "\\n", line_num, column))
            line_num += value.count('\n')
            line_start = match.end()
            continue

        # Ignorar espacios y comentarios
        if kind in ("SKIP", "COMMENT"):
            continue

        # Normalizar a mayúsculas
        if kind in ("KEYWORD", "BOOL", "MODO", "COLOR"):
            value = value.upper()

        # Error léxico
        if kind == "MISMATCH":
            raise RuntimeError(
                f"Token inválido '{value}' en línea {line_num}, columna {column}"
            )

        tokens.append(Token(kind, value, line_num, column))

    return tokens


# =========================
# TEST
# =========================

if __name__ == "__main__":
    with open("prueba.txt", "r", encoding="utf-8") as f:
        code = f.read()

    tokens = lexer(code)

    print("=== TOKENS ===\n")

    for token in tokens:
        print(f"{token.type:10} -> {token.value}")