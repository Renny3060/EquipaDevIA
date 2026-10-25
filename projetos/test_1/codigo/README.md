# Programa de Soma de Números

Este programa em Python solicita três e quatro números ao utilizador e exibe a soma de cada conjunto de números.

## Instalação

Este programa não requer instalação adicional. Basta ter Python instalado em seu sistema.

## Execução

Para executar o programa, abra um terminal e navegue até o diretório onde o arquivo `main.py` está localizado. Em seguida, execute o seguinte comando:

```bash
python main.py
```

## Estrutura de Pastas

O projeto possui a seguinte estrutura de pastas:

```
.
├── main.py
└── utils
    ├── input_utils.py
    └── math_utils.py
```

- `main.py`: Ponto de entrada do programa.
- `utils/input_utils.py`: Contém funções para solicitar e validar entrada do usuário.
- `utils/math_utils.py`: Contém funções matemáticas.

## Exemplos de Uso

### Exemplo 1: Soma de Três Números

```bash
python main.py
Insira três números (1/3): 1
Insira três números (2/3): 2
Insira três números (3/3): 3
A soma dos três números é: 6.0
```

### Exemplo 2: Soma de Quatro Números

```bash
python main.py
Insira quatro números (1/4): 1
Insira quatro números (2/4): 2
Insira quatro números (3/4): 3
Insira quatro números (4/4): 4
A soma dos quatro números é: 10.0
```

### Exemplo 3: Entrada Inválida

```bash
python main.py
Insira três números (1/3): a
Entrada inválida. Por favor, insira um número.
Insira três números (1/3): 1
Insira três números (2/3): 2
Insira três números (3/3): 3
A soma dos três números é: 6.0
```

### Exemplo 4: Entrada Incompleta

```bash
python main.py
Insira três números (1/3): 1
Insira três números (2/3): 2
A soma dos três números é: 3.0
```

### Exemplo 5: Entrada Excedente

```bash
python main.py
Insira três números (1/3): 1
Insira três números (2/3): 2
Insira três números (3/3): 3
Insira três números (4/3): 4
Insira três números (5/3): 5
A soma dos três números é: 6.0
```

## Contribuição

Contribuições são bem-vindas! Por favor, abra um problema ou envie um pull request para melhorar este projeto.

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.
