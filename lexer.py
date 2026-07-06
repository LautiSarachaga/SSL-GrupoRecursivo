from tokens import Token


class Lexer:
    def __init__(self, codigo):
        self.codigo = codigo
        self.pos = 0
        self.linea = 1
        self.columna = 1

    def ver_siguiente(self):                    #
        if self.pos + 1 < len(self.codigo):     #   mira el siguiente caracter
            return self.codigo[self.pos + 1]    #
        return ""

    def leer_palabra(self):                     #
        inicio_col = self.columna               #   guarda la columna inicial de la palabra
        valor = ""                              #   

        while (
            self.pos < len(self.codigo)
            and (self.codigo[self.pos].isalnum() or self.codigo[self.pos] == "_")
        ):
            valor += self.codigo[self.pos]      #   
            self.pos += 1                       #   aca guarda la palabra completa
            self.columna += 1                   #

        v_up = valor.upper()                    #

        KEYWORDS = ["WHEN", "IF", "THEN", "ELSE", "DO", "END", "EVERY", "AND", "OR", "NOT"]
        BOOLEANS = ["TRUE", "FALSE", "ON", "OFF"]       #   guardamos palabras reservadas 
        DISCRETOS = ["FRIO", "CALOR", "VENT"]
        NOMBRES = ["WHITE", "RED", "YELLOW", "BLUE"]

        if v_up in KEYWORDS:
            return Token("KEYWORD", v_up, self.linea, inicio_col)
        
        if v_up in BOOLEANS:
            return Token("BOOL", v_up, self.linea, inicio_col)
            
        if v_up in DISCRETOS:
            return Token("DISCRETO", v_up, self.linea, inicio_col)
            
        if v_up in NOMBRES:
            
            return Token("NOMBRE", valor, self.linea, inicio_col)

        return Token("IDENT", valor, self.linea, inicio_col)

    def leer_numero_con_unidad(self):
        inicio_col = self.columna
        num = ""

        if self.codigo[self.pos] == "-":
            num += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        while (
            self.pos < len(self.codigo)
            and (self.codigo[self.pos].isdigit() or self.codigo[self.pos] == ".")
        ):
            num += self.codigo[self.pos]
            self.pos += 1
            self.columna += 1

        char = self.codigo[self.pos] if self.pos < len(self.codigo) else ""

        if char == "°" and self.ver_siguiente() == "C":
            self.pos += 2
            self.columna += 2
            return Token("TEMP", num + "°C", self.linea, inicio_col)

        elif char == "%":
            self.pos += 1
            self.columna += 1
            return Token("PERCENT", num + "%", self.linea, inicio_col)

        elif char == "l" and self.codigo[self.pos:self.pos + 3] == "lux":
            self.pos += 3
            self.columna += 3
            return Token("LUX", num + "lux", self.linea, inicio_col)

        elif char in ["s", "m", "h"]:
            self.pos += 1
            self.columna += 1
            return Token("DURATION", num + char, self.linea, inicio_col)

        raise Exception(
            f"Error Léxico en línea {self.linea}: El número '{num}' no tiene unidad."
        )

    def leer_fecha(self):
            inicio_col = self.columna
            valor = self.codigo[self.pos:self.pos + 10]

            try:
                dia = int(valor[0:2])
                mes = int(valor[3:5])
                anio = int(valor[6:10])

                if not (1 <= dia <= 31) or not (1 <= mes <= 12) or not (1900 <= anio <= 2099):
                    raise Exception(f"Error Léxico en línea {self.linea}: Fecha fuera de rango '{valor}'.")
            except ValueError:
                raise Exception(f"Error Léxico en línea {self.linea}: Formato de fecha inválido '{valor}'.")

            self.pos += 10
            self.columna += 10
            return Token("DATE", valor, self.linea, inicio_col)

    def leer_hora(self):
        inicio_col = self.columna
        
        valor = self.codigo[self.pos:self.pos + 5]

        try:
            
            horas = int(valor[0:2])
            minutos = int(valor[3:5])

            if horas > 23 or minutos > 59:
                raise Exception(f"Error Léxico en línea {self.linea}: Hora inválida '{valor}'.")
                
        except ValueError:

            raise Exception(f"Error Léxico en línea {self.linea}: Formato de hora incorrecto '{valor}'.")

        self.pos += 5
        self.columna += 5

        return Token("TIME", valor, self.linea, inicio_col)

    def leer_operador(self):
        inicio_col = self.columna
        c = self.codigo[self.pos]
        s = self.ver_siguiente()

        if c + s in ["==", "!=", ">=", "<="]:
            self.pos += 2
            self.columna += 2
            return Token("OPERADOR_REL", c + s, self.linea, inicio_col)

        self.pos += 1
        self.columna += 1

        if c in [">", "<"]:
            return Token("OPERADOR_REL", c, self.linea, inicio_col)
        if c == "=":
            return Token("ASSIGN", c, self.linea, inicio_col)
        if c == ".":
            return Token("DOT", c, self.linea, inicio_col)
        if c in "()":
            return Token("APAREN" if c == "(" else "CPAREN", c, self.linea, inicio_col)

        if c == ".":

            if self.ver_siguiente() == ".":
                raise Exception(f"Error Léxico en línea {self.linea}: Símbolo '..' no válido.")
            return Token("DOT", c, self.linea, inicio_col)

        return None

    def leer_string(self):
        inicio_col = self.columna

        self.pos += 1
        self.columna += 1

        valor = ""

        while self.pos < len(self.codigo):

            if self.codigo[self.pos] == '"':
                self.pos += 1
                self.columna += 1

                return Token("STRING", valor, self.linea, inicio_col)

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

        if valor.count("@") != 1:
            raise Exception(f"Error Léxico en línea {self.linea}: Email inválido '{valor}'.")

        usuario, dominio = valor.split("@")

        if not usuario or not dominio or "." not in dominio:
            raise Exception(f"Error Léxico en línea {self.linea}: Email inválido '{valor}'.")

        caracteres_permitidos = "_.-+"
        for char in usuario + dominio:
            if not (char.isalnum() or char in caracteres_permitidos):
                raise Exception(f"Error Léxico en línea {self.linea}: Carácter no permitido en email '{char}'.")

        extension = dominio.split(".")[-1]
        if not (2 <= len(extension) <= 4) or not extension.isalpha():
            raise Exception(f"Error Léxico en línea {self.linea}: Extensión de email inválida '{extension}'.")

        return Token("EMAIL", valor, self.linea, inicio_col)

    def tokenizar(self):
        tokens = []

        while self.pos < len(self.codigo):

            char = self.codigo[self.pos]

            if char.isspace():
                if char == "\n":
                    self.linea += 1
                    self.columna = 1
                else:
                    self.columna += 1
                self.pos += 1
                continue

            if (char == "/" and self.ver_siguiente() == "/"):
                while self.pos < len(self.codigo) and self.codigo[self.pos] != "\n":
                    self.pos += 1
                continue

            if char == '"':
                tokens.append(self.leer_string())

            elif (char.isalpha() and char.isascii()) or char == "_":

                i = self.pos
                es_email = False

                while i < len(self.codigo) and not self.codigo[i].isspace():
                    if self.codigo[i] == "@":
                        es_email = True
                        break
                    i += 1

                if es_email:
                    tokens.append(self.leer_email())
                else:
                    tokens.append(self.leer_palabra())

            elif char.isdigit():

                es_fecha = (
                    self.pos + 9 < len(self.codigo)
                    and self.codigo[self.pos + 2] == "/"
                    and self.codigo[self.pos + 5] == "/"
                )
                es_hora = (
                    self.pos + 4 < len(self.codigo)
                    and self.codigo[self.pos + 2] == ":" 
                    and self.codigo[self.pos + 1].isdigit()
                    and self.codigo[self.pos + 3].isdigit()
                )

                if es_fecha:
                    tokens.append(self.leer_fecha())
                elif es_hora:
                    tokens.append(self.leer_hora())
                else:
                    tokens.append(self.leer_numero_con_unidad())

            elif char == "-" and self.ver_siguiente().isdigit():
                tokens.append(self.leer_numero_con_unidad())

            elif char in "=!><.()":
                tokens.append(self.leer_operador())

            else:
                raise Exception(
                    f"Error Léxico en línea {self.linea}: Símbolo '{char}' no sirve."
                )
        return tokens