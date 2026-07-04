from lexer import Lexer

try:
    with open("entrada.txt", "r", encoding="utf-8") as archivo:
        codigo = archivo.read()
    lexer = Lexer(codigo)

    tokens_encontrados = lexer.tokenizar()
    
    print("Tokens generados exitosamente:")
    for t in tokens_encontrados:
        print(f"Línea: {t.linea:<2}  Col: {t.columna:<2} | Tipo: {t.tipo:<12} | Valor: {repr(t.valor)}")

except Exception as e:
    # Manda error si algun token no se reconoce
    print(f"¡Se detectó un problema! {e}")