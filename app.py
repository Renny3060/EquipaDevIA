import os
import time
from pathlib import Path

import streamlit as st

import checks
import config
import llm
from agents import AGENTES
from pipeline import Fabrica
from workspace import Project, list_projects, slug

st.set_page_config(page_title="Fábrica de Software Local", page_icon="🏭", layout="wide")

ICONES = {"fase": "🧭", "agente": "🤖", "ficheiro": "📄", "erro": "❌",
          "ok": "✅", "teste": "🧪", "info": "ℹ️"}
LANG = {"py": "python", "js": "javascript", "ts": "typescript", "html": "html", "css": "css",
        "json": "json", "sql": "sql", "sh": "bash", "md": "markdown", "java": "java",
        "go": "go", "rs": "rust", "cs": "csharp", "cpp": "cpp", "c": "c", "php": "php"}


@st.cache_resource
def runs() -> dict:
    return {}


def ocupado() -> bool:
    return any(f.running for f in runs().values())


# ---------------- barra lateral ----------------
if "_goto" in st.session_state:
    st.session_state["sel_proj"] = st.session_state.pop("_goto")

with st.sidebar:
    st.title("🏭 Fábrica Local")
    if llm.is_up():
        st.success("Ollama ligado")
    else:
        st.error("Ollama desligado. Abre uma CMD e corre `ollama serve`.")
    modelos = llm.list_models() or [config.DEFAULT_MODEL]
    idx = modelos.index(config.DEFAULT_MODEL) if config.DEFAULT_MODEL in modelos else 0
    model = st.selectbox("Modelo", modelos, index=idx)
    num_ctx = st.select_slider("Contexto (num_ctx)", [4096, 8192, 16384, 32768], value=8192,
                               help="Mais contexto = melhor memória, mas mais RAM/VRAM e mais lento.")
    nivel = st.radio("Rigor", ["Rápido", "Normal", "Completo"], index=1,
                     help="Rápido: só escreve e verifica sintaxe. Normal: + integração + testes. "
                          "Completo: + revisão, segurança e performance em cada ficheiro (bem mais lento).")
    st.divider()
    escolha = st.selectbox("Projeto", ["➕ Novo projeto"] + list_projects(), key="sel_proj")
    if ocupado():
        st.warning("A equipa está a trabalhar...")


def lancar(p: Project, metodo: str, *args):
    f = Fabrica(Project(p.name), nivel, model, num_ctx)
    runs()[p.name] = f
    getattr(f, metodo)(*args)
    st.rerun()


# ---------------- novo projeto ----------------
if escolha == "➕ Novo projeto":
    st.header("Novo projeto")
    with st.form("novo"):
        nome = st.text_input("Nome do projeto", placeholder="ex.: gestor_tarefas")
        linguagem = st.text_input("Linguagem / stack", value="Python",
                                  placeholder="ex.: Python + SQLite, JavaScript (Node), C#...")
        prompt = st.text_area("O que queres que a equipa construa?", height=200,
                              placeholder="Descreve o programa com o máximo de detalhe possível...")
        ok = st.form_submit_button("🚀 Iniciar equipa", disabled=ocupado())
    if ok:
        if not nome.strip() or not prompt.strip():
            st.error("Preenche o nome e o pedido.")
        elif slug(nome) in list_projects():
            st.error("Já existe um projeto com esse nome.")
        else:
            p = Project(nome)
            p.state.update(prompt=prompt.strip(), language=linguagem.strip() or "Python")
            p.save()
            f = Fabrica(Project(p.name), nivel, model, num_ctx)
            runs()[p.name] = f
            f.iniciar_novo()
            st.session_state["_goto"] = p.name
            st.rerun()
    st.stop()

# ---------------- projeto existente ----------------
p = Project(escolha)
st.header(f"📁 {p.name}")
st.caption(f"{p.state['language']} · criado em {p.state['criado']} · estado: **{p.state['status']}**")


@st.fragment(run_every=2)
def painel_progresso(nome: str):
    pr = Project(nome)
    fab = runs().get(nome)
    a_correr = bool(fab and fab.running)
    chave = f"was_{nome}"
    if a_correr:
        st.session_state[chave] = True
    elif st.session_state.get(chave):
        st.session_state[chave] = False
        st.rerun()

    if a_correr:
        st.progress(fab.progress, text=fab.label)
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**A trabalhar:** {fab.current_agent}")
        if c2.button("⏹ Parar", key="parar"):
            fab.stop.set()
        with st.expander("Ver o que o agente está a escrever", expanded=False):
            st.code(fab.live[-1800:] or "...", language=None)
    else:
        st.progress(1.0 if pr.state["status"].startswith("concluído") else 0.0, text=pr.state["status"])

    eventos = pr.read_log(300)[::-1]
    erros = [e for e in eventos if e["kind"] == "erro"]
    if erros:
        with st.expander(f"❌ Erros ocorridos ({len(erros)})"):
            for e in erros[:15]:
                st.markdown(f"`{e['t']}` **{e['agent']}**")
                st.code(e["msg"][:1500], language=None)
    st.subheader("Atividade")
    with st.container(height=380):
        for e in eventos:
            msg = e["msg"].replace("\n", " ⏎ ")[:260]
            st.markdown(f"`{e['t']}` {ICONES.get(e['kind'], '•')} **{e['agent']}** {msg}")


tab_prog, tab_fich, tab_exec, tab_alt, tab_plano, tab_eq = st.tabs(
    ["📊 Progresso", "📁 Ficheiros", "▶️ Executar e testes", "🛠️ Alterar / corrigir bug",
     "📝 Plano e relatório", "👥 Equipa"])

with tab_prog:
    pendentes = [i for i in p.state["plan"] if not i.get("done")]
    if (pendentes or p.state["status"] in ("interrompido", "erro")) and not ocupado() and p.state["prompt"]:
        if st.button("▶️ Retomar de onde ficou"):
            lancar(p, "iniciar_retomar")
    painel_progresso(p.name)

with tab_fich:
    arvore = p.tree()
    if not arvore:
        st.info("Ainda não há ficheiros.")
    else:
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown("**Estrutura**")
            st.code("\n".join(arvore), language=None)
            if st.button("📂 Abrir pasta") and os.name == "nt":
                os.startfile(str(p.code))
        with c2:
            arq = st.selectbox("Ficheiro", arvore)
            conteudo = p.read_file(arq)
            st.code(conteudo, language=LANG.get(Path(arq).suffix.lstrip("."), None), line_numbers=True)
            with st.expander("✏️ Editar manualmente"):
                novo = st.text_area("Conteúdo", conteudo, height=350, key=f"ed_{p.name}_{arq}")
                if st.button("💾 Guardar", disabled=ocupado()):
                    p.write_file(arq, novo)
                    st.success("Guardado (a versão anterior fica em .fabrica/versoes).")

with tab_exec:
    saida_key = f"saida_{p.name}"
    st.markdown("**Ambiente**")
    if st.button("📦 Preparar ambiente (venv + pip install)", disabled=ocupado()):
        with st.spinner("A instalar dependências..."):
            st.session_state[saida_key] = checks.setup_env(p)
    run_cmd = st.text_input("Comando de execução", p.state.get("run_cmd") or "python main.py")
    test_cmd = st.text_input("Comando de testes (vazio = automático em Python)", p.state.get("test_cmd", ""))
    timeout = st.number_input("Timeout (segundos)", 5, 600, 30)
    c1, c2 = st.columns(2)
    if c1.button("▶️ Executar", disabled=ocupado()):
        p.state.update(run_cmd=run_cmd, test_cmd=test_cmd)
        p.save()
        with st.spinner("A executar..."):
            st.session_state[saida_key] = checks.run(checks.adapt_cmd(p, run_cmd), p.code, int(timeout))["out"]
    if c2.button("🧪 Correr testes", disabled=ocupado()):
        cmd = test_cmd or "python -m unittest discover -s tests -t . -v"
        with st.spinner("A testar..."):
            st.session_state[saida_key] = checks.run(checks.adapt_cmd(p, cmd), p.code, 180)["out"]
    saida = st.session_state.get(saida_key)
    if saida:
        st.code(saida, language=None)
        if st.button("🐞 Enviar este resultado à equipa para corrigir", disabled=ocupado()):
            lancar(p, "iniciar_alteracao", "Corrige o erro/problema que aparece na execução ou nos testes.", saida)

with tab_alt:
    st.markdown("Descreve uma funcionalidade nova, uma melhoria ou um bug. A equipa decide que ficheiros mexer.")
    pedido = st.text_area("Pedido", height=150)
    usar_erro = st.checkbox("Incluir o último resultado/erro do separador Executar",
                            value=bool(st.session_state.get(f"saida_{p.name}")))
    if st.button("🚀 Enviar à equipa", disabled=ocupado() or not pedido.strip()):
        erro = st.session_state.get(f"saida_{p.name}", "") if usar_erro else ""
        lancar(p, "iniciar_alteracao", pedido.strip(), erro)
    if p.state["historico"]:
        st.subheader("Histórico de pedidos")
        for h in p.state["historico"][::-1]:
            st.markdown(f"- `{h['quando']}` {h['pedido']}")

with tab_plano:
    if p.state["relatorio"]:
        st.subheader("Relatório final")
        st.write(p.state["relatorio"])
    st.subheader("Plano de ficheiros")
    if p.state["plan"]:
        st.dataframe([{"ficheiro": i["path"], "descrição": i["desc"],
                       "feito": "✅" if i.get("done") else "⏳"} for i in p.state["plan"]],
                     use_container_width=True)
    with st.expander("Requisitos"):
        st.markdown(p.state["requirements"] or "—")
    with st.expander("Contrato de interfaces"):
        st.markdown(p.state["contract"] or "—")

with tab_eq:
    st.markdown("Os 20 papéis da equipa (todos usam o mesmo modelo local, cada um com instruções próprias):")
    for a in AGENTES.values():
        st.markdown(f"{a.emoji} **{a.nome}** — {a.funcao}")