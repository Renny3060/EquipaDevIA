# utils/input_utils.py

def solicitar_numeros(mensagem: str, quantidade: int) -> list[float]:
    numeros = []
    while len(numeros) < quantidade:
        try:
            numero = float(input(f"{mensagem} ({len(numeros) + 1}/{quantidade}): "))
            numeros.append(numero)
        except ValueError:
            print("Entrada inválida. Por favor, insira um número.")
    return numeros

def validar_entrada(entrada: str) -> bool:
    try:
        float(entrada)
        return True
    except ValueError:
        return False
