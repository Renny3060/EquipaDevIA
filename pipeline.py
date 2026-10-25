import re
import threading
import time

import checks
import config
import llm
import parsing
from agents import AGENTES
from workspace import Project


class Cancelado(Exception):
    pass


def agente_para(path: str) -> str:
    p = path.lower()
    nome = p.split("/")[-1]
    if (nome.startswith("test_") or nome.endswith(("_test.py", ".test.js", ".spec.js", ".test.ts"))
            or p.startswith(("tests/", "test/"))):
        return "qa"
    if nome == "readme.md" or p.startswith("docs/"):
        return "docs"
    if (nome in ("requirements.txt", "dockerfile", "docker-compose.yml", "package.json",
                 "makefile", ".gitignore", ".env.example", "pyproject.toml")
            or nome.endswith((".bat", ".sh", ".yml", ".yaml", ".toml"))):
        return "devops"
    if p.endswith((".html", ".css", ".jsx", ".tsx", ".vue", ".svelte")) or any(
            x in p for x in ("frontend/", "ui/", "templates/", "static/", "gui", "views/")):
        return "frontend"
    if p.endswith(".sql") or any(x in p for x in ("models", "schema", "database", "db/", "migrations", "repository")):
        return "dados"
    if any(x in p for x in ("api", "routes", "controllers", "client", "integra", "service")):
        return "api"
    if any(x in p for x in ("utils", "helpers", "lib/", "core/", "common", "config", "constants")):
        return "core"
    return "backend"


class Fabrica:
    def __init__(self, project: Project, nivel="Normal", model=None, num_ctx=None, max_fixes=3):
        self.p = project
        self.nivel = nivel
        self.model = model or config.DEFAULT_MODEL
        self.num_ctx = num_ctx or config.DEFAULT_NUM_CTX
        self.max_fixes = max_fixes
        self.stop = threading.Event()
        self.running = False
        self.live = ""
        self.current_agent = ""
        self.progress = 0.0
        self.label = ""
        self.problemas: list[str] = []

    # ---------- infraestrutura ----------
    def prog(self, frac, label):
        self.progress = min(max(frac, 0.0), 1.0)
        self.label = label
        self.p.log("fase", label)
        self.p.save()

    def ask(self, chave: str, tarefa: str) -> str:
        if self.stop.is_set():
            raise Cancelado()
        ag = AGENTES[chave]
        self.current_agent = f"{ag.emoji} {ag.nome}"
        self.live = ""
        self.p.log("agente", "a trabalhar...", ag.nome)

        def on_tok(t):
            if self.stop.is_set():
                raise Cancelado()
            self.live = (self.live + t)[-4000:]

        return llm.chat(ag.system(self.p.state["language"]), tarefa, model=self.model,
                        num_ctx=self.num_ctx, on_token=on_tok)

    def ctx(self, contrato=True) -> str:
        s = self.p.state
        t = [f"LINGUAGEM/STACK: {s['language']}",
             f"PEDIDO ORIGINAL:\n{s['prompt']}",
             f"REQUISITOS:\n{s['requirements'][:2500]}"]
        if s["plan"]:
            t.append("ESTRUTURA PLANEADA:\n" + "\n".join(f"- {i['path']}: {i['desc']}" for i in s["plan"]))
        if contrato and s["contract"]:
            t.append("CONTRATO DE INTERFACES:\n" + s["contract"][:3500])
        return "\n\n".join(t)

    def assinaturas(self, excluir="") -> str:
        return checks.signatures(self.p, excluir) or "(ainda nenhum ficheiro escrito)"

    # ---------- arranque em thread ----------
    def _executar(self, fn, *args):
        self.running = True
        self.stop.clear()
        self.problemas = []
        self.p.state["status"] = "a trabalhar"
        self.p.save()
        try:
            fn(*args)
            self.p.state["status"] = "concluído com avisos" if self.problemas else "concluído"
            self.progress, self.label = 1.0, "Terminado"
            self.p.log("ok", "Trabalho terminado." +
                       (f" Avisos: {len(self.problemas)}" if self.problemas else ""))
        except Cancelado:
            self.p.state["status"] = "interrompido"
            self.p.log("info", "Interrompido pelo utilizador.")
        except Exception as e:
            self.p.state["status"] = "erro"
            self.p.log("erro", f"{type(e).__name__}: {e}")
        finally:
            self.running = False
            self.current_agent = ""
            self.p.save()

    def _lancar(self, fn, *args):
        threading.Thread(target=self._executar, args=(fn, *args), daemon=True).start()

    def iniciar_novo(self):
        self._lancar(self._novo)

    def iniciar_retomar(self):
        self._lancar(self._retomar)

    def iniciar_alteracao(self, pedido: str, erro: str = ""):
        self._lancar(self._alterar, pedido, erro)

    # ---------- fluxos ----------
    def _novo(self):
        self.planear()
        self.implementar()
        self.verificar()
        self.finalizar()

    def _retomar(self):
        self.planear()
        self.implementar()
        self.verificar()
        self.finalizar()

    # ---------- fase 1: planeamento ----------
    def planear(self):
        s = self.p.state
        if s["plan"] and s["requirements"]:
            return
        pedido = s["prompt"]
        self.prog(0.02, "Planeamento: requisitos")
        req = self.ask(
            "po",
            f"Pedido do cliente:\n{pedido}\n\nEscreve os requisitos de forma concisa: objetivo principal, "
            "até 5 funcionalidades chave (lista numerada), o que NÃO faz parte, e critérios de aceitação curtos. "
            "ATENÇÃO: Sê extremamente breve. Não repitas texto, não inventes listas longas e termina a resposta rapidamente.",
        )
        ana = self.ask("analista", f"Pedido:\n{pedido}\n\nRequisitos:\n{req}\n\n"
                                   "Lista regras de negócio, casos limite e erros que têm de ser tratados. Máx. 250 palavras.")
        self.prog(0.08, "Planeamento: interface")
        ux = self.ask("ux", f"Pedido:\n{pedido}\n\nRequisitos:\n{req}\n\nSe o projeto tem interface (janela, web ou "
                            "terminal interativo) descreve ecrãs, fluxo e componentes. Se não, responde apenas SEM INTERFACE. Máx. 200 palavras.")
        self.prog(0.10, "Planeamento: dados")
        dados = self.ask("dados", f"Pedido:\n{pedido}\n\nRequisitos:\n{req}\n\nDefine entidades/estruturas de dados e como "
                                  "se guardam (ficheiros, SQLite...). Se não aplicável responde NÃO APLICÁVEL. Máx. 200 palavras.")
        s["requirements"] = (f"## Requisitos\n{req}\n\n## Regras e casos limite\n{ana}\n\n"
                             f"## Interface\n{ux}\n\n## Dados\n{dados}")
        self.p.save()

        self.prog(0.13, "Planeamento: arquitetura")
        base = (f"{self.ctx(contrato=False)}\n\nDefine a estrutura de ficheiros do projeto, com subpastas organizadas por "
                f"responsabilidade. Máximo {config.MAX_FILES} ficheiros, em ORDEM DE DEPENDÊNCIA (base primeiro, ponto de "
                "entrada por último). NÃO incluas README, requirements nem testes (são criados depois).\n"
                "FORMATO ESTRITO, uma linha por ficheiro, sem mais texto:\n"
                "FILE: caminho/relativo.ext | descrição curta | deps: ficheiro1, ficheiro2\n"
                "Na última linha: RUN: comando para executar o projeto (ex.: python main.py)")
        itens = []
        for tentativa in range(3):
            extra = "" if tentativa == 0 else "\n\nATENÇÃO: responde SÓ com linhas 'FILE: ...' e a linha 'RUN: ...'."
            out = self.ask("arquiteto", base + extra)
            itens = [i for i in parsing.parse_linhas(out) if i["tipo"] == "FILE"][:config.MAX_FILES]
            if itens:
                s["run_cmd"] = parsing.parse_run(out)
                break
        if not itens:
            itens = [{"path": "main.py", "desc": "programa principal", "deps": []}]
            s["run_cmd"] = "python main.py"
        s["plan"] = [{"path": i["path"], "desc": i["desc"], "deps": i["deps"], "done": False} for i in itens]
        self.p.save()

        self.prog(0.17, "Planeamento: contrato de interfaces")
        s["contract"] = self.ask("techlead", f"{self.ctx(contrato=False)}\n\nDefine o CONTRATO DE INTERFACES: para cada "
                                             "ficheiro da estrutura lista as funções/classes/constantes públicas com assinatura EXATA "
                                             "(nomes, parâmetros, tipos, retorno) e uma linha sobre o que fazem; indica quem importa quem. "
                                             "Formato:\n### caminho\n- assinatura — descrição\nMáx. 600 palavras. Só ficheiros da estrutura.")
        self.p.save()

    # ---------- fase 2: implementação ----------
    def implementar(self):
        plano = self.p.state["plan"]
        total = len(plano)
        for i, item in enumerate(plano):
            if item.get("done") and self.p.exists(item["path"]):
                continue
            self.prog(0.2 + 0.5 * i / max(total, 1), f"A escrever {item['path']} ({i + 1}/{total})")
            self.escrever(item["path"], item["desc"], item.get("deps", []))
            item["done"] = True
            self.p.save()

    def escrever(self, path, desc, deps=(), existente=None):
        chave = agente_para(path)
        partes = [self.ctx(), "API REAL DOS FICHEIROS JÁ ESCRITOS:\n" + self.assinaturas(path)]
        for d in list(deps)[:3]:
            if self.p.exists(d):
                partes.append(f"CONTEÚDO DE {d}:\n```\n{self.p.read_file(d, 3000)}\n```")
        verbo = "Reescreve (com as alterações pedidas)" if existente else "Escreve"
        if existente:
            partes.append(f"CONTEÚDO ATUAL DE {path}:\n```\n{existente[:8000]}\n```")
        tarefa = ("\n\n".join(partes) + f"\n\nTAREFA: {verbo} o ficheiro `{path}` — {desc}.\n"
                  "Responde SÓ com o conteúdo COMPLETO do ficheiro num único bloco de código. "
                  "Importa dos outros módulos exatamente com os nomes do contrato.")
        codigo = parsing.extract_code(self.ask(chave, tarefa))
        self.p.write_file(path, codigo)
        self.p.log("ficheiro", f"{path} ({len(codigo.splitlines())} linhas)", AGENTES[chave].nome)
        self.corrigir_sintaxe(path)

    def corrigir_sintaxe(self, path):
        for _ in range(2):
            err = checks.check_file(self.p.code, path)
            if not err:
                return
            self.p.log("erro", err, "Verificador")
            self.reparar(err, [path])
        err = checks.check_file(self.p.code, path)
        if err:
            self.problemas.append(err)

    def reparar(self, problema, ficheiros, agente="debugger") -> list[str]:
        ficheiros = [f for f in dict.fromkeys(ficheiros) if self.p.exists(f)][:3]
        partes = [self.ctx(), "API REAL DOS FICHEIROS:\n" + self.assinaturas()]
        for f in ficheiros:
            partes.append(f"FICHEIRO `{f}`:\n```\n{self.p.read_file(f, 6000)}\n```")
        tarefa = ("\n\n".join(partes) + f"\n\nPROBLEMA:\n{problema[-3000:]}\n\n"
                  "Corrige a causa raiz. Devolve APENAS os ficheiros que alteraste, cada um assim:\n"
                  "### FILE: caminho\n```\nconteúdo completo\n```\n"
                  "Se o erro estiver no teste e não no código, corrige o teste.")
        out = self.ask(agente, tarefa)
        blocos = parsing.multi_files(out)
        if not blocos and len(ficheiros) == 1 and "```" in out:
            blocos = [(ficheiros[0], parsing.extract_code(out))]
        alterados = []
        for rel, codigo in blocos:
            if not self.p.exists(rel):
                continue
            antigo = self.p.read_file(rel)
            tinha_erro = bool(checks.check_file(self.p.code, rel))
            self.p.write_file(rel, codigo)
            if checks.check_file(self.p.code, rel) and not tinha_erro:
                self.p.write_file(rel, antigo)  # piorou: reverte
                self.p.log("info", f"Correção de {rel} rejeitada (introduziu erro de sintaxe).", AGENTES[agente].nome)
                continue
            alterados.append(rel)
            self.p.log("ficheiro", f"{rel} corrigido", AGENTES[agente].nome)
        return alterados

    # ---------- fase 3: verificação ----------
    def verificar(self):
        self.prog(0.72, "Verificação: comunicação entre ficheiros")
        for _ in range(self.max_fixes):
            issues = checks.python_import_issues(self.p)
            if not issues:
                break
            self.p.log("erro", f"{len(issues)} problema(s) de integração:\n" +
                       "\n".join(m for _, _, m in issues[:8]), "Integrador")
            por_ficheiro: dict[str, list] = {}
            for rel, alvo, msg in issues:
                por_ficheiro.setdefault(rel, []).append((alvo, msg))
            for rel, lista in por_ficheiro.items():
                alvos = [a for a, _ in lista]
                self.reparar("\n".join(m for _, m in lista) +
                             "\nAjusta o import/uso OU adiciona o que falta no módulo de destino, seguindo o contrato.",
                             [rel] + alvos, agente="integrador")
        else:
            restantes = checks.python_import_issues(self.p)
            if restantes:
                self.problemas.append("Integração: " + restantes[0][2])
        if self.nivel == "Completo":
            self.revisoes()
        if self.nivel != "Rápido":
            self.testes()

    def revisoes(self):
        alvos = [i["path"] for i in self.p.state["plan"]
                 if checks.eh_codigo(i["path"]) and self.p.exists(i["path"])][:10]
        focos = (("revisor", "qualidade, bugs lógicos e consistência com o contrato"),
                 ("seguranca", "segurança (injeção, caminhos, segredos no código, validação de input)"),
                 ("performance", "performance e uso de recursos"))
        for k, (chave, foco) in enumerate(focos):
            for j, path in enumerate(alvos):
                self.prog(0.76 + 0.08 * (k + j / max(len(alvos), 1)) / 3,
                          f"{AGENTES[chave].nome}: {path}")
                tarefa = (f"{self.ctx()}\n\nAPI REAL:\n{self.assinaturas(path)}\n\nFICHEIRO `{path}`:\n```\n"
                          f"{self.p.read_file(path, 8000)}\n```\n\nRevê este ficheiro com foco em {foco}. "
                          "Se não há problemas relevantes responde exatamente APROVADO. "
                          "Caso contrário devolve o ficheiro COMPLETO corrigido num bloco de código, sem alterar a API pública.")
                out = self.ask(chave, tarefa)
                if "APROVADO" in out[:60].upper():
                    continue
                antigo = self.p.read_file(path)
                self.p.write_file(path, parsing.extract_code(out))
                if checks.check_file(self.p.code, path):
                    self.p.write_file(path, antigo)
                    self.p.log("info", f"Revisão de {path} rejeitada (erro de sintaxe).", AGENTES[chave].nome)
                else:
                    self.p.log("ficheiro", f"{path} melhorado ({foco.split(' ')[0]})", AGENTES[chave].nome)

    def gerar_testes(self):
        tarefa = (f"{self.ctx()}\n\nAPI REAL:\n{self.assinaturas()}\n\nEscreve testes com unittest (biblioteca padrão) "
                  "para a lógica principal, no máximo 3 ficheiros em tests/ (ex.: tests/test_core.py). Importa os módulos a "
                  "partir da raiz do projeto (ex.: from app.core import f). Não testes interface gráfica, rede nem input().\n"
                  "Formato:\n### FILE: tests/test_x.py\n```\ncódigo\n```")
        out = self.ask("qa", tarefa)
        blocos = [(r, c) for r, c in parsing.multi_files(out) if r.startswith("tests/") and r.endswith(".py")]
        if not blocos and "```" in out:
            blocos = [("tests/test_principal.py", parsing.extract_code(out))]
        for rel, cod in blocos[:3]:
            self.p.write_file(rel, cod)
            self.p.log("ficheiro", f"{rel} (teste)", AGENTES["qa"].nome)

    def testes(self):
        s = self.p.state
        cmd = s.get("test_cmd") or ""
        if checks.eh_python(self.p) and not cmd:
            cmd = "python -m unittest discover -s tests -t . -v"
            tem = lambda: any(f.startswith("tests/") and f.endswith(".py") and f != "tests/__init__.py"
                              for f in self.p.tree())
            if not tem():
                self.prog(0.85, "QA: a escrever testes")
                self.gerar_testes()
            if not tem():
                self.p.log("info", "Sem testes para correr.")
                return
        elif not cmd:
            self.p.log("info", "Sem comando de testes definido para esta linguagem (podes definir no separador Executar).")
            return
        entrada = [self.p.state["plan"][-1]["path"]] if self.p.state["plan"] else []
        for r in range(self.max_fixes + 1):
            self.prog(0.88, f"A correr testes (tentativa {r + 1})")
            res = checks.run(checks.adapt_cmd(self.p, cmd), self.p.code, 180)
            if res["ok"] or "Ran 0 tests" in res["out"]:
                self.p.log("teste", "Testes OK ✅\n" + res["out"][-600:])
                return
            self.p.log("teste", "Testes falharam:\n" + res["out"][-1500:])
            if res["ok"] is None or r == self.max_fixes:
                break
            self.reparar(res["out"], checks.traceback_files(res["out"], self.p) or entrada)
        self.problemas.append("Testes a falhar: " + res["out"][-300:])

    # ---------- fase 4: finalização ----------
    def finalizar(self, mudanca=""):
        s = self.p.state
        self.prog(0.92, "Finalização: dependências e documentação")
        run_cmd = s.get("run_cmd") or "python main.py"
        if checks.eh_python(self.p):
            novos = checks.write_requirements(self.p)
            if novos:
                self.p.log("ficheiro", "requirements.txt: " + ", ".join(novos), AGENTES["devops"].nome)
            bat = ('@echo off\ncd /d "%~dp0codigo"\nif not exist "..\\.venv" ( python -m venv ..\\.venv )\n'
                   'call ..\\.venv\\Scripts\\activate\nif exist requirements.txt pip install -r requirements.txt -q\n'
                   f'{run_cmd}\npause\n')
            (self.p.root / "executar.bat").write_text(bat, encoding="utf-8")
        if not mudanca and not self.p.exists("README.md"):
            out = self.ask("docs", f"{self.ctx()}\n\nAPI REAL:\n{self.assinaturas()}\n\nEscreve o README.md: o que é, como "
                                   f"instalar, como executar ({run_cmd}), estrutura de pastas e exemplos de uso. "
                                   "Responde diretamente em Markdown, sem o envolver num bloco de código.")
            self.p.write_file("README.md", parsing.strip_outer_fence(out))
            self.p.log("ficheiro", "README.md", AGENTES["docs"].nome)
        self.prog(0.96, "Finalização: changelog")
        out = self.ask("release", f"Escreve 3 a 6 linhas em lista Markdown para o CHANGELOG sobre: "
                                  f"{mudanca or 'versão inicial do projeto'}.\nFicheiros atuais:\n" + "\n".join(self.p.tree()))
        antigo = re.sub(r"^# Changelog\s*", "", self.p.read_file("CHANGELOG.md"))
        self.p.write_file("CHANGELOG.md", f"# Changelog\n\n## {time.strftime('%Y-%m-%d %H:%M')}\n{out.strip()}\n\n{antigo}")
        s["relatorio"] = self.ask("gestor", f"{self.ctx()}\n\nFicheiros: {', '.join(self.p.tree())}\n"
                                            f"Problemas por resolver: {self.problemas or 'nenhum'}\n"
                                            f"Trabalho feito: {mudanca or 'criação do projeto'}\n\n"
                                            f"Escreve o relatório final para o cliente: o que foi feito, como executar ({run_cmd}) "
                                            "e limitações conhecidas. Máx. 150 palavras.")
        self.p.save()

    # ---------- alterações e bugs ----------
    def _alterar(self, pedido, erro=""):
        s = self.p.state
        s["historico"].append({"quando": time.strftime("%Y-%m-%d %H:%M"), "pedido": pedido})
        self.prog(0.05, "A analisar o pedido")
        tarefa = (f"{self.ctx()}\n\nPEDIDO DE ALTERAÇÃO/BUG:\n{pedido}\n" +
                  (f"\nERRO REPORTADO:\n{erro[-3000:]}\n" if erro else "") +
                  "\nDecide que ficheiros mudam. Formato estrito, uma linha por ficheiro, sem mais texto:\n"
                  "EDIT: caminho existente | o que mudar\n"
                  "FILE: caminho novo | para que serve | deps: ficheiro1\n")
        itens = parsing.parse_linhas(self.ask("techlead", tarefa))
        itens = [i for i in itens if i["tipo"] == "FILE" or self.p.exists(i["path"])]
        if not itens:  # fallback: traceback, ficheiros citados, ou ponto de entrada
            alvo = checks.traceback_files(erro, self.p) if erro else []
            alvo += [f for f in self.p.tree() if f in pedido or f.split("/")[-1] in pedido]
            alvo = alvo or ([s["plan"][-1]["path"]] if s["plan"] else [])
            itens = [{"tipo": "EDIT", "path": a, "desc": pedido, "deps": []} for a in dict.fromkeys(alvo)][:3]
        for k, it in enumerate(itens):
            self.prog(0.1 + 0.5 * k / len(itens), f"A alterar {it['path']}")
            novo = not self.p.exists(it["path"])
            self.escrever(it["path"], f"{it['desc']} (pedido do utilizador: {pedido})", it["deps"],
                          existente=None if novo else self.p.read_file(it["path"]))
            if novo and not any(x["path"] == it["path"] for x in s["plan"]):
                s["plan"].append({"path": it["path"], "desc": it["desc"], "deps": it["deps"], "done": True})
        self.verificar()
        self.finalizar(mudanca=pedido)