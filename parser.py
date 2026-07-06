import os

class Parser:

    def __init__(self, tokens, nombre_archivo="salida.smart"):
        self.tokens = tokens
        self.pos = 0
        self.nombre_archivo = nombre_archivo
        
        self.sensores = {}
        self.actuadores = {}

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
        
        token_valor = self.actual()
        tipo_valor = token_valor.tipo if token_valor else None
        
        valor = self.parsear_valor()
        
        dispositivo_norm = dispositivo.lower()
        atributo_norm = atributo.lower()
        
        prefijo_encontrado = None
        for prefijo in self.reglas_actuadores.keys():
            if dispositivo_norm.startswith(prefijo):
                prefijo_encontrado = prefijo
                break
        
        if not prefijo_encontrado:
            raise Exception(f"Error Semántico en línea {token_valor.linea}: El dispositivo '{dispositivo}' no es un actuador válido o reconocido para asignación.")
        
        atributos_permitidos = self.reglas_actuadores[prefijo_encontrado]
        if atributo_norm not in atributos_permitidos:
            raise Exception(f"Error Semántico en línea {token_valor.linea}: No se puede modificar el atributo '{atributo}' de '{dispositivo}' (No existe o es de Solo Lectura).")
            
        tipo_esperado = atributos_permitidos[atributo_norm]
        if tipo_valor != tipo_esperado:
            raise Exception(f"Error Semántico en línea {token_valor.linea}: '{dispositivo}.{atributo}' espera un valor de tipo {tipo_esperado}, pero recibió un {tipo_valor} ('{valor}').")
            
        if tipo_esperado == "PERCENT":
            
            valor_numerico = float(valor.replace("%", ""))
            if valor_numerico < 0 or valor_numerico > 100:
                raise Exception(f"Error Semántico en línea {token_valor.linea}: El porcentaje '{valor}' está fuera de rango para '{dispositivo}.{atributo}'. Debe estar entre 0% y 100%.")
                
        elif tipo_esperado == "TEMP" and prefijo_encontrado == "aire_":
            valor_numerico = float(valor.replace("°C", ""))
            if valor_numerico < 16 or valor_numerico > 30:
                raise Exception(f"Error Semántico en línea {token_valor.linea}: La temperatura objetivo '{valor}' está fuera de rango. Debe ser entre 16°C y 30°C.")

        
        # aca empieza a traducir a html
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
        token_izq = self.actual()
        op_izq_dispositivo = self.consumir("IDENT").valor
        op_izq_atributo = None
        
        if self.actual() and self.actual().tipo == "DOT":
            self.consumir("DOT")
            op_izq_atributo = self.consumir("IDENT").valor
            
        self.consumir("OPERADOR_REL")
        
        token_der = self.actual()
        tipo_der = token_der.tipo if token_der else None
        
        op_der = self.parsear_valor()
        
        # validaciones 
        if not op_izq_atributo:
            
            dispositivo_norm = op_izq_dispositivo.lower()
            
            if dispositivo_norm.startswith("sensor_luz"):
                if tipo_der != "LUX":
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: '{op_izq_dispositivo}' espera tipo LUX, pero recibió {tipo_der}.")
                valor_num = float(op_der.replace("lux", ""))
                if valor_num < 0 or valor_num > 1000:
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: El valor '{op_der}' está fuera de rango (0 a 1000 lux).")

            elif dispositivo_norm.startswith("sensor_temp"):
                if tipo_der != "TEMP":
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: '{op_izq_dispositivo}' espera tipo TEMP, pero recibió {tipo_der}.")
                valor_num = float(op_der.replace("°C", ""))
                if valor_num < -10.0 or valor_num > 50.0:
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: El valor '{op_der}' está fuera de rango (-10.0°C a 50.0°C).")

            elif dispositivo_norm.startswith("sensor_humedad"):
                if tipo_der != "PERCENT":
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: '{op_izq_dispositivo}' espera tipo PERCENT, pero recibió {tipo_der}.")
                valor_num = float(op_der.replace("%", ""))
                if valor_num < 0 or valor_num > 100:
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: El valor '{op_der}' está fuera de rango (0% a 100%).")
                    
            elif dispositivo_norm.startswith("sensor_movimiento") or dispositivo_norm.startswith("sensor_humo"):

                if tipo_der != "BOOL":
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: '{op_izq_dispositivo}' espera un valor BOOL (TRUE/FALSE), pero recibió un {tipo_der} ('{op_der}').")
        else:
            
            dispositivo_norm = op_izq_dispositivo.lower()
            atributo_norm = op_izq_atributo.lower()
            
            tipos_comparacion = {
                "foco": {"estado": "BOOL", "brillo": "PERCENT", "color": "NOMBRE"},
                "aire": {"estado": "BOOL", "modo": "DISCRETO", "temp_objetivo": "TEMP", "temp_obj": "TEMP", "temp_act": "TEMP"},
                "persiana": {"posicion": "PERCENT", "posición": "PERCENT"},
                "cerradura": {"estado": "BOOL"},
                "altavoz": {"volumen": "PERCENT", "mute": "BOOL", "mensaje": "STRING", "email": "EMAIL", "email_notif": "EMAIL"},
                "alarma": {"estado": "BOOL", "activada": "BOOL"},
                "reloj": {"hora": "TIME", "fecha": "DATE"}
            }
            
            prefijo_encontrado = None
            for prefijo in tipos_comparacion.keys():
                if dispositivo_norm.startswith(prefijo):
                    prefijo_encontrado = prefijo
                    break
            
            if prefijo_encontrado and atributo_norm in tipos_comparacion[prefijo_encontrado]:
                tipo_esperado = tipos_comparacion[prefijo_encontrado][atributo_norm]
                if tipo_der != tipo_esperado:
                    raise Exception(f"Error Semántico en línea {token_izq.linea}: '{op_izq_dispositivo}.{op_izq_atributo}' requiere comparar con un {tipo_esperado}, pero recibió {tipo_der}.")

        if not op_izq_atributo:
            self.sensores[op_izq_dispositivo] = op_der
            
        return {"tipo": "COMPARACION"}

    def parsear_valor(self):
        t = self.actual()
        if t is None:
            raise Exception("Error Sintáctico: Se esperaba un valor.")
            
        tipos_valor = [
            "IDENT", "BOOL", "TEMP", "PERCENT", "LUX", "TIME", 
            "DATE", "DURATION", "STRING", "EMAIL", "NOMBRE", "DISCRETO"
        ]
        
        if t.tipo in tipos_valor:
            self.pos += 1
            return t.valor
            
        raise Exception(f"Error Sintáctico en línea {t.linea}: Valor no válido '{t.valor}'.")

    def generar_html(self):
        base = os.path.splitext(self.nombre_archivo)[0]
        archivo_salida = f"{base}.html"

        html = "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n"
        html += "    <meta charset=\"UTF-8\">\n"
        html += "    <title>Smart Home Dashboard</title>\n"
        html += "</head>\n<body>\n"

        if self.sensores:
            html += "    <div style=\"border: 1px solid green; padding: 20px; margin-bottom: 20px;\">\n"
            for sensor, valor in self.sensores.items():
                
                html += f"        <h2>{sensor}: {valor}</h2>\n"
            html += "    </div>\n\n"

        if self.actuadores:
            for actuador, atributos in self.actuadores.items():
                html += "    <div style=\"border: 1px solid gray; padding: 20px; margin-bottom: 20px;\">\n"
                
                html += f"        <h1>{actuador}</h1>\n"
                
                html += "        <ul>\n"
                
                for attr, val in atributos.items():
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
            
        print(f"\nArchivo HTML generado exitosamente: {archivo_salida}\n")