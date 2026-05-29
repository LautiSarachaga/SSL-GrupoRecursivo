from lexer import Lexer

with open("prueba1.txt", "r", encoding="utf-8") as f:
    codigo = f.read()

lexer = Lexer(codigo)

tokens = lexer.tokenizar()

print("\n=== TOKENS ===\n")

for token in tokens:
    print(token)