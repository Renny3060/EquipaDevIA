# 🏭 EquipaDevIA — Fábrica de Software Local

[![Licença: MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-green.svg)](LICENSE)

Uma "equipa de software" de **20 agentes de IA** que corre 100% no teu computador. Descreves o programa que queres, e a equipa planeia, escreve (com subpastas e vários ficheiros), verifica, testa, documenta e entrega o projeto — tudo através de um modelo local servido pelo [Ollama](https://ollama.com), sem enviar código para a cloud.

A interface é feita em [Streamlit](https://streamlit.io) e o modelo por defeito é o `qwen2.5-coder:7b`.

---

## ✨ O que faz

- **Gera projetos completos** com estrutura de pastas, vários ficheiros e dependências entre eles.
- **Planeia antes de programar**: requisitos, regras de negócio, interface, dados, arquitetura e um *contrato de interfaces* (assinaturas exatas entre módulos).
- **Verifica o que escreve**: sintaxe, coerência dos imports entre ficheiros e testes automáticos.
- **Auto-corrige-se**: quando algo falha, um agente depurador tenta reparar (com limite de tentativas) e as correções que pioram o código são rejeitadas e revertidas.
- **Aceita pedidos de alteração e bugs** depois de o projeto estar criado.
- **Guarda versões** de todos os ficheiros que são substituídos.
- **Retoma** de onde ficou se for interrompido ou der erro.

---

## 📋 Requisitos

| Requisito | Notas |
|---|---|
| Windows | O `run.bat` e a opção "Abrir pasta" foram pensados para Windows |
| Python 3.11 | O `run.bat` tenta `py -3.11` e usa `python` como alternativa |
| [Ollama](https://ollama.com) | A correr em `http://localhost:11434` |
| Modelo `qwen2.5-coder:7b` | `ollama pull qwen2.5-coder:7b` |
| RAM/VRAM | Quanto maior o contexto (`num_ctx`), mais memória é necessária |

Dependências Python (`requirements.txt`):

```
streamlit>=1.37
requests
```

---

## 🚀 Como executar

1. Instala o Ollama e descarrega o modelo:
   ```cmd
   ollama pull qwen2.5-coder:7b
   ```
2. Numa CMD, deixa o Ollama a correr:
   ```cmd
   ollama serve
   ```
3. Noutra CMD, na pasta do projeto, executa:
   ```cmd
   run.bat
   ```
   O script cria o ambiente virtual (`venv`), instala as dependências, abre o browser em `http://localhost:8501` e arranca o Streamlit.

> Se o Ollama estiver desligado, a barra lateral da aplicação mostra um aviso a vermelho.

---

## 🖥️ Como usar a aplicação

### Barra lateral

- **Modelo** — escolhe entre os modelos instalados no Ollama.
- **Contexto (`num_ctx`)** — 4096, 8192, 16384 ou 32768. Mais contexto = melhor memória, mas mais lento e com mais consumo de RAM/VRAM.
- **Rigor** — define quanto a equipa verifica o trabalho:

  | Nível | O que faz |
  |---|---|
  | **Rápido** | Escreve os ficheiros, verifica a sintaxe e a coerência dos imports |
  | **Normal** *(por defeito)* | Rápido + gera e corre testes automáticos |
  | **Completo** | Normal + revisão de código, segurança e performance em cada ficheiro (bastante mais lento) |

- **Projeto** — escolhe um projeto existente ou cria um novo.

### Novo projeto

Preenche o **nome**, a **linguagem/stack** (por defeito Python) e a **descrição** do que queres construir. Quanto mais detalhe, melhor o resultado. Carrega em **🚀 Iniciar equipa**.

### Separadores de um projeto

| Separador | Para que serve |
|---|---|
| 📊 **Progresso** | Barra de progresso, agente ativo, texto que está a ser escrito em direto, erros e registo de atividade. Tem botões para **parar** e **retomar** |
| 📁 **Ficheiros** | Árvore de ficheiros, visualização com realce de sintaxe, edição manual e botão para abrir a pasta |
| ▶️ **Executar e testes** | Preparar o ambiente (venv + pip), executar o programa, correr testes e enviar o erro à equipa para corrigir |
| 🛠️ **Alterar / corrigir bug** | Pede uma funcionalidade nova, uma melhoria ou a correção de um bug. Mostra o histórico de pedidos |
| 📝 **Plano e relatório** | Relatório final, plano de ficheiros, requisitos e contrato de interfaces |
| 👥 **Equipa** | Lista dos 20 papéis |

---

## ⚙️ Como funciona por dentro

O trabalho passa por quatro fases, orquestradas pela classe `Fabrica` em `pipeline.py`:

### 1. Planeamento
1. **Product Owner** transforma o pedido em requisitos e critérios de aceitação.
2. **Analista de Requisitos** acrescenta regras de negócio, casos limite e erros.
3. **Designer UX/UI** descreve a interface (ou responde `SEM INTERFACE`).
4. **Arquiteto de Dados** define entidades e persistência (ou `NÃO APLICÁVEL`).
5. **Arquiteto de Software** define a estrutura de ficheiros (máx. 30), ordenada por dependência.
6. **Tech Lead** escreve o contrato de interfaces com as assinaturas exatas.

### 2. Implementação
Cada ficheiro é escrito por **o agente mais adequado ao tipo de ficheiro** (função `agente_para`): testes → QA, README/docs → Documentação, configs e scripts → DevOps, HTML/CSS/componentes → Frontend, SQL/modelos → Dados, rotas/serviços → API, utilitários → Core, e o resto → Backend.

Cada agente recebe o pedido, os requisitos, o contrato e as assinaturas reais dos ficheiros já escritos. Depois de cada ficheiro, a sintaxe é verificada e, se falhar, o **Debugger** repara (até 2 vezes).

### 3. Verificação
- **Integrador** deteta imports locais que apontam para nomes que não existem e corrige-os (até 3 rondas).
- No nível **Completo**, o **Revisor**, o **Engenheiro de Segurança** e o **Engenheiro de Performance** revêem cada ficheiro. Se estiver tudo bem, respondem `APROVADO`.
- Nos níveis **Normal** e **Completo**, o **QA** escreve testes `unittest` (máx. 3 ficheiros em `tests/`), a equipa corre-os e o Debugger tenta corrigir as falhas.

### 4. Finalização
- Gera o `requirements.txt` automaticamente a partir dos imports (com aliases como `cv2` → `opencv-python`).
- Cria o `executar.bat` do projeto gerado.
- O **Engenheiro de Documentação** escreve o `README.md`.
- O **Release Manager** atualiza o `CHANGELOG.md`.
- O **Gestor de Projeto** escreve o relatório final com o que foi feito, como executar e as limitações conhecidas.

### Pedidos de alteração
O **Tech Lead** analisa o pedido (e o erro, se houver) e decide quais ficheiros editar (`EDIT:`) ou criar (`FILE:`). Os ficheiros são reescritos, voltam a passar pela verificação e o changelog é atualizado.

---

## 👥 Os 20 agentes

Todos usam o mesmo modelo local; o que muda são as instruções de cada papel.

| | Agente | Função |
|---|---|---|
| 🧑‍💼 | Gestor de Projeto | Responsável pela entrega e pelo relatório final |
| 🎯 | Product Owner | Requisitos claros e critérios de aceitação |
| 🔎 | Analista de Requisitos | Regras de negócio, casos limite e erros |
| 🏛️ | Arquiteto de Software | Estrutura de pastas e ficheiros |
| 🧭 | Tech Lead | Contratos de interfaces e decisão de que ficheiros mudam |
| 🎨 | Designer UX/UI | Fluxos, ecrãs e componentes |
| 🗄️ | Arquiteto de Dados | Modelos de dados e persistência |
| ⚙️ | Engenheiro Backend | Lógica de negócio e pontos de entrada |
| 🖼️ | Engenheiro Frontend | Interfaces web, desktop ou terminal |
| 🔌 | Engenheiro de Integração/API | Rotas, clientes e serviços |
| 🧱 | Engenheiro de Core/Utilitários | Código partilhado e configuração |
| 🚀 | Engenheiro DevOps | Dependências, scripts e Docker |
| 🛡️ | Engenheiro de Segurança | Injeção, caminhos perigosos, segredos |
| ⚡ | Engenheiro de Performance | Ineficiências graves |
| 🧐 | Revisor de Código | Bugs lógicos e consistência com o contrato |
| 🧪 | Engenheiro de QA | Testes automáticos |
| 🐞 | Debugger | Causa raiz de erros e correções mínimas |
| 🔗 | Integrador | Imports, nomes e assinaturas entre ficheiros |
| 📚 | Engenheiro de Documentação | READMEs claros |
| 📦 | Release Manager | Entradas de changelog |

---

## 📁 Estrutura do repositório

```
EquipaDevIA/
├── app.py            # Interface Streamlit
├── pipeline.py       # Orquestração das fases e dos agentes (classe Fabrica)
├── agents.py         # Definição dos 20 agentes e respetivos prompts
├── llm.py            # Cliente do Ollama (streaming, tentativas, deteção de repetições)
├── checks.py         # Verificação de sintaxe/imports, execução, venv, requirements
├── parsing.py        # Extração de código e de ficheiros das respostas do modelo
├── workspace.py      # Gestão de projetos, estado, registo e versões
├── config.py         # Configuração (modelo, contexto, temperatura, limites)
├── main.py           # Protótipo antigo em CrewAI com um só agente
├── requirements.txt
├── run.bat           # Arranque no Windows
└── projetos/         # Projetos gerados
    └── <nome_do_projeto>/
        ├── codigo/            # Código gerado (inclui tests/, README.md, CHANGELOG.md...)
        ├── executar.bat       # Script para executar o projeto gerado
        ├── .venv/             # Ambiente virtual do projeto gerado
        └── .fabrica/
            ├── estado.json    # Pedido, requisitos, plano, contrato, relatório, histórico
            ├── log.jsonl      # Registo de atividade
            └── versoes/       # Cópias dos ficheiros antes de serem substituídos
```

---

## 🔧 Configuração

Em `config.py`:

| Opção | Valor por defeito | Descrição |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Endereço do Ollama |
| `DEFAULT_MODEL` | `qwen2.5-coder:7b` | Modelo usado por defeito |
| `DEFAULT_NUM_CTX` | `8192` | Tamanho do contexto |
| `TEMPERATURE` | `0.2` | Temperatura (baixa = respostas mais consistentes) |
| `MAX_FILES` | `30` | Máximo de ficheiros por projeto |

Em `llm.py`, cada resposta está limitada a 4096 tokens (`num_predict`) e tem `repeat_penalty` de 1.15. Se o modelo entrar num ciclo de repetição, a geração é interrompida automaticamente.

---

## ⚠️ Limitações e avisos

- **Executa código gerado por IA na tua máquina**, sem sandbox (`shell=True`). Revê o código antes de o executares, sobretudo em projetos que mexam em ficheiros, rede ou dados importantes.
- A qualidade depende do modelo. Um modelo de 7B pode errar; por isso existem as verificações automáticas e a possibilidade de pedir correções, mas o resultado final deve sempre ser revisto.
- As verificações mais profundas (coerência de imports, testes automáticos e `requirements.txt`) são específicas de **Python**. Para JavaScript só há verificação de sintaxe (e só se o Node estiver instalado). Para outras linguagens podes definir o comando de testes manualmente.
- Só corre **uma equipa de cada vez**.
- O `main.py` é um protótipo antigo baseado em CrewAI. Precisa de `crewai` instalado, que **não** está no `requirements.txt`, e não é usado pela aplicação.

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**. Consulta o ficheiro [LICENSE](LICENSE) para ver o texto completo.

Podes usar, copiar, modificar e distribuir este software livremente, desde que mantenhas o aviso de copyright e a licença. O software é fornecido "tal como está", sem qualquer garantia.
