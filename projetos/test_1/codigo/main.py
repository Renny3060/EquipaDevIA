# main.py
from utils.input_utils import solicitar_numeros
from utils.math_utils import calcular_soma

def main():
    try:
        # Solicitar três números
        numeros_três = solicitar_numeros("Insira três números", 3)
        soma_três = calcular_soma(numeros_três)
        print(f"A soma dos três números é: {soma_três}")

        # Solicitar quatro números
        numeros_quatro = solicitar_numeros("Insira quatro números", 4)
        soma_quatro = calcular_soma(numeros_quatro)
        print(f"A soma dos quatro números é: {soma_quatro}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()
