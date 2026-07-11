from lexer import Lexer
from parser import Parser
import os

def mostrar_tokens(tokens):
    print("\nTokens encontrados:\n")
    for t in tokens:
        print(f"Línea: {t.linea:<2} Col: {t.columna:<2} | Tipo: {t.tipo:<12} | Valor: {repr(t.valor)}")
    print(f"\nSe encontraron {len(tokens)} token(s).\n")

def analizar_archivo():
    nombre = input("\nIngrese el nombre del archivo: ").strip()

    if not os.path.isfile(nombre):
        print("\nEl archivo no existe.\n")
        return

    try:
        with open(nombre, "r", encoding="utf-8") as archivo:
            codigo = archivo.read()

        print("\n--- INICIANDO ANÁLISIS LÉXICO ---")
        lexer = Lexer(codigo)
        tokens = lexer.tokenizar()
        
        if lexer.errores:
            print("\n*** SE ENCONTRARON ERRORES LÉXICOS ***")
            for err in lexer.errores:
                print(f" -> {err}")

        print("\n--- INICIANDO ANÁLISIS SINTÁCTICO Y TRADUCCIÓN ---")
        parser = Parser(tokens, nombre)
        parser.parsear_programa()

        if parser.errores:
            print("\n*** SE ENCONTRARON ERRORES SINTÁCTICOS/SEMÁNTICOS ***")
            for err in parser.errores:
                print(f" -> {err}")

        if not lexer.errores and not parser.errores:
            print("\nAnálisis finalizado exitosamente sin errores.")
        else:
            print("\nAnálisis finalizado. Se reportaron errores, pero se generó el HTML de las partes válidas.")

    except Exception as e:
        print(f"\nError fatal inesperado! {e}\n")

def analizar_interactivo():
    print("\nModo interactivo.")
    print("Escriba 'salir' para finalizar este modo.\n")

    while True:
        texto = input(">> ")
        if texto.lower() == "salir":
            return
        if texto.strip() == "":
            continue

        try:
            lexer = Lexer(texto)
            tokens = lexer.tokenizar()
            
            if lexer.errores:
                for err in lexer.errores:
                    print(f" -> {err}")
            mostrar_tokens(tokens)

        except Exception as e:
            print(f"\nError! {e}\n")

def otro_analisis():
    while True:
        respuesta = input("¿Desea realizar otro análisis? (S/N): ").strip().upper()
        if respuesta in ("S", "SI", "SÍ"):
            return True
        if respuesta in ("N", "NO"):
            return False
        print("Respuesta inválida. Ingrese S o N.\n")

def main():
    while True:
        print("=" * 40)
        print("     ANALIZADOR LÉXICO Y SINTÁCTICO")
        print("=" * 40)
        print("1) Analizar texto interactivo")
        print("2) Analizar archivo")
        print("0) Salir")

        opcion = input("\nSeleccione una opción: ").strip()

        if opcion == "0":
            break
        elif opcion == "1":
            analizar_interactivo()
        elif opcion == "2":
            analizar_archivo()
        else:
            print("\nOpción inválida.\n")
            continue

        if not otro_analisis():
            break

if __name__ == "__main__":
    main()