import os

class Parser:
    # Ahora el Parser recibe el nombre del archivo para saber cómo nombrar el .html
    def __init__(self, tokens, nombre_archivo="salida.smart"):
        self.tokens = tokens
        self.pos = 0
        self.nombre_archivo = nombre_archivo
        
        self.sensores = {}
        self.actuadores = {}

        # --- NUEVA TABLA DE VALIDACIÓN SEMÁNTICA ---
        # Define qué atributos se pueden escribir y qué tipo de token exigen
        self.reglas_actuadores = {
            "foco_": {"estado": "BOOL", "brillo": "PERCENT", "color": "NOMBRE"},
            "aire_": {"estado": "BOOL", "modo": "DISCRETO", "temp_objetivo": "TEMP", "temp_obj": "TEMP"},
            "persiana_": {"posicion": "PERCENT"},
            "cerradura_": {"estado": "BOOL"},
            "altavoz_": {"volumen": "PERCENT", "mute": "BOOL", "mensaje": "STRING", "email": "EMAIL", "email_notif": "EMAIL"},
            "alarma_": {"estado": "BOOL", "activada": "BOOL"}
        }

    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consumir(self, tipo_esperado, valor_esperado=None):
        t = self.actual()
        
        if t is None:
            raise Exception(f"Error Sintáctico: Fin de archivo inesperado. Faltan tokens de tipo '{tipo_esperado}'.")
            
        if t.tipo == tipo_esperado:
            if valor_esperado and t.valor.upper() != valor_esperado.upper():
                raise Exception(
                    f"Error Sintáctico en línea {t.linea}: Se esperaba '{valor_esperado}', se encontró '{t.valor}'."
                )
            self.pos += 1
            return t
            
        raise Exception(
            f"Error Sintáctico en línea {t.linea}: Se esperaba tipo '{tipo_esperado}', se encontró '{t.tipo}' ('{t.valor}')."
        )

    def parsear_programa(self):
        instrucciones = []
        while self.actual() is not None:
            instrucciones.append(self.parsear_instruccion())
            
        # Cuando termina de parsear todo el programa con éxito, genera el HTML
        self.generar_html()
        
        return instrucciones

    def parsear_instruccion(self):
        t = self.actual()
        
        if t.tipo == "KEYWORD":
            if t.valor == "WHEN":
                return self.parsear_when()
            elif t.valor == "EVERY":
                return self.parsear_every()
            elif t.valor == "IF":
                return self.parsear_if()
        
        if t.tipo == "IDENT":
            return self.parsear_asignacion()
            
        raise Exception(f"Error Sintáctico en línea {t.linea}: Instrucción no reconocida al inicio de línea '{t.valor}'.")

    def parsear_when(self):
        self.consumir("KEYWORD", "WHEN")
        condicion = self.parsear_condicion()
        self.consumir("KEYWORD", "DO")
        
        acciones = []
        while self.actual() is not None and not (self.actual().tipo == "KEYWORD" and self.actual().valor == "END"):
            acciones.append(self.parsear_instruccion())
            
        self.consumir("KEYWORD", "END")
        return {"tipo": "WHEN", "condicion": condicion, "acciones": acciones}

    def parsear_every(self):
        self.consumir("KEYWORD", "EVERY")
        tiempo = self.consumir("DURATION")
        self.consumir("KEYWORD", "DO")
        
        acciones = []
        while self.actual() is not None and not (self.actual().tipo == "KEYWORD" and self.actual().valor == "END"):
            acciones.append(self.parsear_instruccion())
            
        self.consumir("KEYWORD", "END")
        return {"tipo": "EVERY", "tiempo": tiempo.valor, "acciones": acciones}

    def parsear_if(self):
        self.consumir("KEYWORD", "IF")
        condicion = self.parsear_condicion()
        self.consumir("KEYWORD", "THEN")
        
        acciones_then = []
        while self.actual() is not None and self.actual().valor not in ["ELSE", "END"]:
            acciones_then.append(self.parsear_instruccion())
            
        acciones_else = []
        if self.actual() is not None and self.actual().valor == "ELSE":
            self.consumir("KEYWORD", "ELSE")
            while self.actual() is not None and self.actual().valor != "END":
                acciones_else.append(self.parsear_instruccion())
                
        self.consumir("KEYWORD", "END")
        return {"tipo": "IF"}

    def parsear_asignacion(self):
        dispositivo = self.consumir("IDENT").valor
        self.consumir("DOT")
        atributo = self.consumir("IDENT").valor
        self.consumir("ASSIGN")
        
        # 1. Capturamos el TIPO de token antes de consumirlo para validarlo
        token_valor = self.actual()
        tipo_valor = token_valor.tipo if token_valor else None
        
        # 2. Consumimos el valor como lo hacías normalmente
        valor = self.parsear_valor()
        
        # --- LÓGICA DE VALIDACIÓN SEMÁNTICA ---
        
        # Normalizamos a minúsculas para que sea case-insensitive según los requerimientos
        dispositivo_norm = dispositivo.lower()
        atributo_norm = atributo.lower()
        
        # A. Identificar a qué familia (prefijo) pertenece el dispositivo
        prefijo_encontrado = None
        for prefijo in self.reglas_actuadores.keys():
            if dispositivo_norm.startswith(prefijo):
                prefijo_encontrado = prefijo
                break
        
        if not prefijo_encontrado:
            raise Exception(f"Error Semántico en línea {token_valor.linea}: El dispositivo '{dispositivo}' no es un actuador válido o reconocido para asignación.")
        
        # B. Validar que el atributo exista y permita escritura
        atributos_permitidos = self.reglas_actuadores[prefijo_encontrado]
        if atributo_norm not in atributos_permitidos:
            raise Exception(f"Error Semántico en línea {token_valor.linea}: No se puede modificar el atributo '{atributo}' de '{dispositivo}' (No existe o es de Solo Lectura).")
            
        # C. Validar que el TIPO del token ingresado coincida con el requerido por la tabla
        tipo_esperado = atributos_permitidos[atributo_norm]
        if tipo_valor != tipo_esperado:
            raise Exception(f"Error Semántico en línea {token_valor.linea}: '{dispositivo}.{atributo}' espera un valor de tipo {tipo_esperado}, pero recibió un {tipo_valor} ('{valor}').")
            
        # ----------------------------------------
        
        # --- TRADUCCIÓN AL HTML EN TIEMPO REAL ---
        if dispositivo not in self.actuadores:
            self.actuadores[dispositivo] = {}
        self.actuadores[dispositivo][atributo] = valor
        
        return {"tipo": "ASIGNACION"}

    def parsear_condicion(self):
        condicion_izquierda = self.parsear_comparacion()
        
        while self.actual() is not None and self.actual().tipo == "KEYWORD" and self.actual().valor in ["AND", "OR"]:
            self.consumir("KEYWORD")
            self.parsear_comparacion()
            
        return {"tipo": "CONDICION"}

    def parsear_comparacion(self):
        op_izq_dispositivo = self.consumir("IDENT").valor
        op_izq_atributo = None
        
        if self.actual() and self.actual().tipo == "DOT":
            self.consumir("DOT")
            op_izq_atributo = self.consumir("IDENT").valor
            
        self.consumir("OPERADOR_REL")
        op_der = self.parsear_valor()
        
        # --- TRADUCCIÓN AL HTML EN TIEMPO REAL ---
        # Si el operando izquierdo no tiene atributo (no tiene punto), asumimos que es un sensor
        if not op_izq_atributo:
            self.sensores[op_izq_dispositivo] = op_der
            
        return {"tipo": "COMPARACION"}

    def parsear_valor(self):
        t = self.actual()
        if t is None:
            raise Exception("Error Sintáctico: Se esperaba un valor.")
            
        # Agregamos "NOMBRE" y "DISCRETO" a la lista de tipos válidos
        tipos_valor = [
            "IDENT", "BOOL", "TEMP", "PERCENT", "LUX", "TIME", 
            "DATE", "DURATION", "STRING", "EMAIL", "NOMBRE", "DISCRETO"
        ]
        
        if t.tipo in tipos_valor:
            self.pos += 1
            return t.valor
            
        raise Exception(f"Error Sintáctico en línea {t.linea}: Valor no válido '{t.valor}'.")

    # ==========================================
    # LÓGICA DE GENERACIÓN HTML INTEGRADA
    # ==========================================
    def generar_html(self):
        base = os.path.splitext(self.nombre_archivo)[0]
        archivo_salida = f"{base}.html"

        html = "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n"
        html += "    <meta charset=\"UTF-8\">\n"
        html += "    <title>Smart Home Dashboard</title>\n"
        html += "</head>\n<body>\n"

        # REGLA PDF: div con borde de 1px verde y padding 20px para los sensores
        if self.sensores:
            html += "    <div style=\"border: 1px solid green; padding: 20px; margin-bottom: 20px;\">\n"
            for sensor, valor in self.sensores.items():
                # REGLA PDF: Nombre de sensor encerrado entre <h2>[cite: 2]
                html += f"        <h2>{sensor}: {valor}</h2>\n"
            html += "    </div>\n\n"

        # REGLA PDF: div con borde de 1px gris y padding de 20px por cada actuador[cite: 2]
        if self.actuadores:
            for actuador, atributos in self.actuadores.items():
                html += "    <div style=\"border: 1px solid gray; padding: 20px; margin-bottom: 20px;\">\n"
                # REGLA PDF: Nombre del actuador entre tags <h1>[cite: 2]
                html += f"        <h1>{actuador}</h1>\n"
                # REGLA PDF: Atributos como listas <ul> e items <li>[cite: 2]
                html += "        <ul>\n"
                for attr, val in atributos.items():
                    # REGLA PDF: EMAIL traducirse como link <a> con href mailto y "Contactar a <usuario>"[cite: 2]
                    if attr == "email" or "@" in str(val):
                        usuario = str(val).split("@")[0]
                        html += f"            <li>{attr}: <a href=\"mailto:{val}\">Contactar a {usuario}</a></li>\n"
                    else:
                        html += f"            <li>{attr}: {val}</li>\n"
                html += "        </ul>\n"
                html += "    </div>\n"

        html += "</body>\n</html>"

        with open(archivo_salida, "w", encoding="utf-8") as f:
            f.write(html)
            
        print(f"\n📄 Archivo HTML generado exitosamente: {archivo_salida}\n")