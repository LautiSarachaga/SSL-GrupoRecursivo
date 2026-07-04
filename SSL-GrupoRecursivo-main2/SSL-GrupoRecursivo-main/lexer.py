from tokens import Token

class Lexer:
    def __init__(self, codigo):
        # Arranca todo de cero: texto, posición y contadores
        self.codigo = codigo
        self.pos = 0
        self.linea = 1
        self.columna = 1

    def ver_siguiente(self):
        # Chusmea el carácter que sigue sin mover el puntero
        if self.pos + 1 < len(self.codigo):
            return self.codigo[self.pos + 1]
        return ""

    def leer_palabra(self):
        inicio_col = self.columna
        valor = ""

        while (
            self.pos < len(self.codigo)
            and (
                self.codigo[self.pos].isalnum()
                or self.codigo[self.pos] == '_'
            )
        ):
            valor += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        v_up = valor.upper()

        KEYWORDS = [
        "WHEN",
        "IF",
        "THEN",
        "ELSE",
        "DO",
        "END",
        "EVERY",
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

        COLORES = [
            "RED",
            "GREEN",
            "BLUE",
            "WHITE",
            "YELLOW",
            "ORANGE",
            "PURPLE"
        ]

        # Todas las palabras reservadas son KEYWORD
        if v_up in KEYWORDS:
            return Token("KEYWORD", v_up, self.linea, inicio_col)

        if v_up in BOOLS:
            return Token("BOOL", v_up, self.linea, inicio_col)

        if v_up in COLORES:
            return Token("COLOR", v_up, self.linea, inicio_col)

        # Cualquier palabra que empiece con letra es un identificador
        if valor[0].isalpha():
            return Token("IDENT", valor, self.linea, inicio_col)
            
            raise Exception(
                f"Error Léxico en línea {self.linea}: Identificador '{valor}' no permitido."
            )

    def leer_numero_con_unidad(self):
        # Lee números y se asegura que tengan la unidad pegada
        inicio_col = self.columna
        num = ""
        if self.codigo[self.pos] == '-': # Por si es negativo
            num += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        while self.pos < len(self.codigo) and (self.codigo[self.pos].isdigit() or self.codigo[self.pos] == '.'):
            num += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        char = self.codigo[self.pos] if self.pos < len(self.codigo) else ""
        # Mira qué unidad es para armar el token
        if char == '°' and self.ver_siguiente() == 'C':
            self.pos += 2
            self.columna += 2
            return Token("TEMP", num + "°C", self.linea, inicio_col)
        elif char == '%':
            self.pos += 1
            self.columna += 1
            return Token("PERCENT", num + "%", self.linea, inicio_col)
        elif char == 'l' and self.codigo[self.pos:self.pos+3] == "lux":
            self.pos += 3
            self.columna += 3
            return Token("LUX", num + "lux", self.linea, inicio_col)
        elif char in ['s', 'm', 'h']:
            self.pos += 1
            self.columna += 1
            return Token("DURATION", num + char, self.linea, inicio_col)

        raise Exception(f"Error Léxico en línea {self.linea}: El número '{num}' no tiene unidad.")

    def leer_hora(self):
        inicio_col = self.columna

        valor = self.codigo[self.pos:self.pos + 5]

        horas = int(valor[0:2])
        minutos = int(valor[3:5])

        if horas > 23 or minutos > 59:
            raise Exception(
                f"Error Léxico en línea {self.linea}: Hora inválida '{valor}'."
            )

        self.pos += 5
        self.columna += 5

        return Token("TIME", valor, self.linea, inicio_col)

    def leer_operador(self):
        # Maneja los símbolos de uno o dos caracteres (como ==)
        inicio_col = self.columna
        c = self.codigo[self.pos]
        s = self.ver_siguiente()

        if c + s in ["==", "!=", ">=", "<="]:
            self.pos += 2
            self.columna += 2
            return Token("OPERADOR_REL", c + s, self.linea, inicio_col)
        
        self.pos += 1
        self.columna += 1
        if c in [">", "<"]: return Token("OPERADOR_REL", c, self.linea, inicio_col)
        if c == "=": return Token("ASSIGN", c, self.linea, inicio_col)
        if c == ".": return Token("DOT", c, self.linea, inicio_col)
        if c in "()": return Token("APAREN" if c == "(" else "CPAREN", c, self.linea, inicio_col)
        return None

    def leer_string(self):
        inicio_col = self.columna

        # Salta la comilla inicial
        self.pos += 1
        self.columna += 1

        valor = ""

        while self.pos < len(self.codigo):

            if self.codigo[self.pos] == '"':
                self.pos += 1
                self.columna += 1

                return Token(
                    "STRING",
                    valor,
                    self.linea,
                    inicio_col
                )

            valor += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        raise Exception(
            f"Error Léxico en línea {self.linea}: Cadena sin cerrar."
        )

    def leer_email(self):
        inicio_col = self.columna
        valor = ""

        while (
            self.pos < len(self.codigo)
            and not self.codigo[self.pos].isspace()
            and self.codigo[self.pos] not in ['\n', '\r']
        ):
            valor += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        # Validación mínima
        if '@' not in valor:
            raise Exception(
                f"Error Léxico en línea {self.linea}: Email inválido '{valor}'."
            )

        if valor.count('@') != 1:
            raise Exception(
                f"Error Léxico en línea {self.linea}: Email inválido '{valor}'."
            )

        usuario, dominio = valor.split('@')

        if usuario == "" or dominio == "":
            raise Exception(
                f"Error Léxico en línea {self.linea}: Email inválido '{valor}'."
            )

        if '.' not in dominio:
            raise Exception(
                f"Error Léxico en línea {self.linea}: Email inválido '{valor}'."
            )

        return Token("EMAIL", valor, self.linea, inicio_col)


    def tokenizar(self):
    # Bucle principal que recorre todo el archivo
        tokens = []

        while self.pos < len(self.codigo):

            char = self.codigo[self.pos]

            # Ignora espacios y saltos de línea
            if char.isspace():
                if char == '\n':
                    self.linea += 1
                    self.columna = 1
                else:
                    self.columna += 1

                self.pos += 1
                continue

            # Ignora comentarios // y #
            if (char == '/' and self.ver_siguiente() == '/') or char == '#':
                while (
                    self.pos < len(self.codigo)
                    and self.codigo[self.pos] != '\n'
                ):
                    self.pos += 1
                continue

            # Strings
            if char == '"':
                tokens.append(self.leer_string())

            # Palabras e identificadores
            elif char.isalpha() or char == '_':

                i = self.pos
                es_email = False

                while i < len(self.codigo) and not self.codigo[i].isspace():
                    if self.codigo[i] == '@':
                        es_email = True
                        break
                    i += 1

                if es_email:
                    tokens.append(self.leer_email())
                else:
                    tokens.append(self.leer_palabra())

            # Números positivos
            elif char.isdigit():

                es_hora = (
                    self.pos + 4 < len(self.codigo)
                    and self.codigo[self.pos].isdigit()
                    and self.codigo[self.pos + 1].isdigit()
                    and self.codigo[self.pos + 2] in [':', '.']
                    and self.codigo[self.pos + 3].isdigit()
                    and self.codigo[self.pos + 4].isdigit()
                )

                if es_hora:
                    tokens.append(self.leer_hora())
                else:
                    tokens.append(self.leer_numero_con_unidad())

            # Números negativos
            elif char == '-' and self.ver_siguiente().isdigit():
                tokens.append(self.leer_numero_con_unidad())

            # Operadores y símbolos
            elif char in "=!><.()":
                tokens.append(self.leer_operador())

            else:
                raise Exception(
                    f"Error Léxico en línea {self.linea}: Símbolo '{char}' no sirve."
                )

        return tokens