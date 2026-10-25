import os
import re
from crewai import Agent, Crew, Process, Task

# Conexão com o modelo local Ollama
LLM_LOCAL = "ollama/qwen2.5-coder:7b"

# Agente focado unicamente em programar
desenvolvedor = Agent(
    role="Engenheiro de Software",
    goal="Escrever apenas e exclusivamente código Python funcional e limpo para o pedido do utilizador.",
    backstory="És um programador especialista. Respondes APENAS com código Python puro, sem explicações, sem texto antes ou depois e sem markdown.",
    verbose=True,
    llm=LLM_LOCAL,
)


def limpar_codigo(texto: str) -> str:
    """Remove marcas de markdown (```python ... ```) e textos adicionais para deixar apenas código válido."""
    # Procura blocos de código markdown se existirem
    blocos = re.findall(r"```(?:python)?\n(.*?)```", texto, re.DOTALL)
    if blocos:
        return blocos[0].strip()

    # Caso não haja marcação, limpa linhas residuais
    linhas = texto.strip().split("\n")
    linhas_limpas = [
        l for l in linhas if not l.startswith("```") and not l.startswith("###")
    ]
    return "\n".join(linhas_limpas).strip()


if __name__ == "__main__":
    print("=== GERADOR DE CÓDIGO LOCAL ===")
    nome_proj = input("Digita o nome do projeto (ex: teste_1): ").strip()
    if not nome_proj:
        nome_proj = "projeto_teste"

    print("\nDescreve o código que queres criar:")
    prompt_usuario = input("> ").strip()

    # Cria a pasta e define o caminho final do ficheiro
    pasta_destino = os.path.join("projetos", nome_proj)
    os.makedirs(pasta_destino, exist_ok=True)

    ficheiro_temp = os.path.join(pasta_destino, "temp_output.txt")
    ficheiro_final = os.path.join(pasta_destino, "main.py")

    # Tarefa única com instrução rígida para gerar apenas código
    t1 = Task(
        description=(
            f"Cria o código Python completo para este pedido: '{prompt_usuario}'.\n"
            "REGRAS ESTRITAS:\n"
            "- Devolve APENAS o código Python.\n"
            "- NÃO escrevas árvores de diretórios, textos de explicação ou introduções.\n"
            "- O ficheiro tem de ser executável sem erros de sintaxe."
        ),
        expected_output="Código fonte Python funcional.",
        agent=desenvolvedor,
        output_file=ficheiro_temp,
    )

    equipa = Crew(
        agents=[desenvolvedor],
        tasks=[t1],
        process=Process.sequential,
        verbose=True,
    )

    print(f"\n[A GERAR CÓDIGO EM: {ficheiro_final}]...")
    equipa.kickoff()

    # Pós-processamento para garantir que o ficheiro só tem código limpo
    if os.path.exists(ficheiro_temp):
        with open(ficheiro_temp, "r", encoding="utf-8") as f:
            conteudo_bruto = f.read()

        codigo_filtrado = limpar_codigo(conteudo_bruto)

        with open(ficheiro_final, "w", encoding="utf-8") as f:
            f.write(codigo_filtrado)

        # Remove o ficheiro temporário
        os.remove(ficheiro_temp)

    print(
        f"\n Concluído! O ficheiro '{ficheiro_final}' foi criado apenas com código Python executável."
    )