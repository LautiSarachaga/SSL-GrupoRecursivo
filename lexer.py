from tokens import Token

class Lexer:

    KEYWORDS = [
        "WHEN",
        "THEN",
        "ELSE",
        "END",
        "AND",
        "OR",
        "NOT"
    ]

    BOOLS = [
        "ON",
        "OFF",
        "TRUE",
        "FALSE"
    ]

    MODOS = [
        "FRIO",
        "CALOR",
        "VENT"
    ]

    COLORES = [
        "RED",
        "GREEN",
        "BLUE",
        "WHITE",
        "YELLOW"
    ]

    def __init__(self, codigo):

        self.codigo = codigo
        self.pos = 0
        self.linea = 1
        self.columna = 1

    # ==================================================
    # UTILIDADES
    # ==================================================

    def actual(self):

        if self.pos >= len(self.codigo):
            return None

        return self.codigo[self.pos]

    def siguiente(self):

        if self.pos + 1 >= len(self.codigo):
            return None

        return self.codigo[self.pos + 1]

    def avanzar(self):

        if self.actual() == '\n':
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1

        self.pos += 1

    # ==================================================
    # TOKENIZADOR PRINCIPAL
    # ==================================================

    def tokenizar(self):

        tokens = []

        while self.actual() is not None:

            c = self.actual()

            # ------------------------------------------
            # ESPACIOS
            # ------------------------------------------

            if c == ' ' or c == '\t':
                self.avanzar()
                continue

            # ------------------------------------------
            # NUEVA LINEA
            # ------------------------------------------

            if c == '\n':

                tokens.append(
                    Token("NEWLINE", "\\n", self.linea, self.columna)
                )

                self.avanzar()
                continue

            # ------------------------------------------
            # COMENTARIOS //
            # ------------------------------------------

            if c == '/' and self.siguiente() == '/':

                while self.actual() is not None and self.actual() != '\n':
                    self.avanzar()

                continue

            # ------------------------------------------
            # IDENTIFICADORES / KEYWORDS
            # ------------------------------------------

            if c.isalpha() or c == '_':
                tokens.append(self.leer_identificador())
                continue

            # ------------------------------------------
            # NUMEROS
            # ------------------------------------------

            if c.isdigit():
                tokens.append(self.leer_numero())
                continue

            # ------------------------------------------
            # STRINGS
            # ------------------------------------------

            if c == '"':
                tokens.append(self.leer_string())
                continue

            # ------------------------------------------
            # OPERADORES
            # ------------------------------------------

            if c == '=':

                if self.siguiente() == '=':
                    tokens.append(
                        Token("EQ", "==", self.linea, self.columna)
                    )

                    self.avanzar()
                    self.avanzar()

                else:

                    tokens.append(
                        Token("ASSIGN", "=", self.linea, self.columna)
                    )

                    self.avanzar()

                continue

            if c == '!':

                if self.siguiente() == '=':

                    tokens.append(
                        Token("NEQ", "!=", self.linea, self.columna)
                    )

                    self.avanzar()
                    self.avanzar()
                    continue

                else:
                    raise Exception("Operador inválido !")

            if c == '>':

                if self.siguiente() == '=':

                    tokens.append(
                        Token("GTE", ">=", self.linea, self.columna)
                    )

                    self.avanzar()
                    self.avanzar()

                else:

                    tokens.append(
                        Token("GT", ">", self.linea, self.columna)
                    )

                    self.avanzar()

                continue

            if c == '<':

                if self.siguiente() == '=':

                    tokens.append(
                        Token("LTE", "<=", self.linea, self.columna)
                    )

                    self.avanzar()
                    self.avanzar()

                else:

                    tokens.append(
                        Token("LT", "<", self.linea, self.columna)
                    )

                    self.avanzar()

                continue

            # ------------------------------------------
            # PUNTO
            # ------------------------------------------

            if c == '.':

                tokens.append(
                    Token("DOT", ".", self.linea, self.columna)
                )

                self.avanzar()
                continue

            # ------------------------------------------
            # PARENTESIS
            # ------------------------------------------

            if c == '(':

                tokens.append(
                    Token("LPAREN", "(", self.linea, self.columna)
                )

                self.avanzar()
                continue

            if c == ')':

                tokens.append(
                    Token("RPAREN", ")", self.linea, self.columna)
                )

                self.avanzar()
                continue

            # ------------------------------------------
            # ERROR
            # ------------------------------------------

            raise Exception(
                f"Carácter inválido '{c}' "
                f"en línea {self.linea}, columna {self.columna}"
            )

        return tokens

    # ==================================================
    # IDENTIFICADORES
    # ==================================================

    def leer_identificador(self):

        linea = self.linea
        columna = self.columna

        lexema = ""

        while self.actual() is not None:

            c = self.actual()

            if c.isalnum() or c == '_':
                lexema += c
                self.avanzar()
            else:
                break

        mayus = lexema.upper()

        # KEYWORDS

        if mayus in self.KEYWORDS:
            return Token("KEYWORD", mayus, linea, columna)

        # BOOL

        if mayus in self.BOOLS:
            return Token("BOOL", mayus, linea, columna)

        # MODOS

        if mayus in self.MODOS:
            return Token("MODO", mayus, linea, columna)

        # COLORES

        if mayus in self.COLORES:
            return Token("COLOR", mayus, linea, columna)

        return Token("IDENT", lexema, linea, columna)

    # ==================================================
    # NUMEROS
    # ==================================================

    def leer_numero(self):

        linea = self.linea
        columna = self.columna

        numero = ""
        tiene_punto = False

        while self.actual() is not None:

            c = self.actual()

            if c.isdigit():

                numero += c
                self.avanzar()

            elif c == '.' and not tiene_punto:

                tiene_punto = True
                numero += c
                self.avanzar()

            else:
                break

        # ------------------------------------------
        # TEMPERATURA
        # ------------------------------------------

        if self.actual() == '°':

            self.avanzar()

            if self.actual() == 'C':

                self.avanzar()

                return Token(
                    "TEMP",
                    numero + "°C",
                    linea,
                    columna
                )

            else:
                raise Exception("Se esperaba C después de °")

        # ------------------------------------------
        # PORCENTAJE
        # ------------------------------------------

        if self.actual() == '%':

            self.avanzar()

            return Token(
                "PERCENT",
                numero + "%",
                linea,
                columna
            )

        return Token(
            "NUMBER",
            numero,
            linea,
            columna
        )

    # ==================================================
    # STRINGS
    # ==================================================

    def leer_string(self):

        linea = self.linea
        columna = self.columna

        self.avanzar()

        texto = ""

        while self.actual() is not None and self.actual() != '"':

            texto += self.actual()
            self.avanzar()

        if self.actual() != '"':
            raise Exception("String sin cerrar")

        self.avanzar()

        return Token(
            "STRING",
            texto,
            linea,
            columna
        )