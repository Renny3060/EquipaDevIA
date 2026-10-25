import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EXT_CODIGO = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cs", ".go", ".rs",
              ".cpp", ".c", ".h", ".php", ".rb", ".kt", ".swift", ".html",
              ".css", ".sql", ".sh", ".bat", ".lua"}
ALIAS_PIP = {"cv2": "opencv-python", "PIL": "pillow", "yaml": "pyyaml",
             "bs4": "beautifulsoup4", "sklearn": "scikit-learn",
             "dotenv": "python-dotenv", "dateutil": "python-dateutil",
             "serial": "pyserial", "docx": "python-docx", "fitz": "pymupdf",
             "jwt": "pyjwt", "flask_cors": "flask-cors"}
SIG_RE = re.compile(
    r"^\s*(?:async\s+def|def|class|function|export\s+(?:default\s+)?(?:async\s+)?"
    r"(?:function|class|const|let|interface|type)|public\s|func\s|fn\s|pub\s|"
    r"interface\s|type\s|module\.exports|[A-Z_]{3,}\s*=)")


def eh_codigo(rel: str) -> bool:
    return Path(rel).suffix.lower() in EXT_CODIGO and not rel.startswith("tests/")


def eh_python(p) -> bool:
    if "python" in p.state.get("language", "").lower():
        return True
    return sum(f.endswith(".py") for f in p.tree()) > len(p.tree()) / 2


def check_file(code_dir, rel: str) -> str:
    f = Path(code_dir) / rel
    try:
        txt = f.read_text(encoding="utf-8")
    except Exception as e:
        return f"Não consigo ler {rel}: {e}"
    if not txt.strip():
        return f"O ficheiro {rel} está vazio."
    if rel.endswith(".py"):
        try:
            ast.parse(txt)
        except SyntaxError as e:
            return f"SyntaxError em {rel}, linha {e.lineno}: {e.msg}\n>>> {(e.text or '').strip()}"
    elif rel.endswith(".json"):
        try:
            json.loads(txt)
        except ValueError as e:
            return f"JSON inválido em {rel}: {e}"
    elif rel.endswith((".js", ".mjs", ".cjs")) and shutil.which("node"):
        r = subprocess.run(["node", "--check", str(f)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=30)
        if r.returncode:
            return f"Erro de sintaxe JS em {rel}:\n{r.stderr[-800:]}"
    return ""


def _definidos(arv) -> set:
    nomes = set()
    for n in arv.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nomes.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        nomes.add(x.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            nomes.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                nomes.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.If, ast.Try, ast.With)):
            for x in ast.walk(n):
                if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    nomes.add(x.name)
                elif isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                    nomes.add(x.id)
    return nomes


def _mapa_modulos(p) -> dict:
    mapa = {}
    for r in (r for r in p.tree() if r.endswith(".py")):
        if r.endswith("/__init__.py"):
            mapa[r[:-12].replace("/", ".")] = r
        elif r != "__init__.py":
            mapa[r[:-3].replace("/", ".")] = r
    return mapa


def python_import_issues(p) -> list[tuple[str, str, str]]:
    """Imports locais que apontam para nomes que não existem."""
    mapa = _mapa_modulos(p)
    cache = {}

    def defs(rel):
        if rel not in cache:
            try:
                cache[rel] = _definidos(ast.parse(p.read_file(rel)))
            except SyntaxError:
                cache[rel] = None
        return cache[rel]

    problemas = []
    for r in mapa.values():
        try:
            arv = ast.parse(p.read_file(r))
        except SyntaxError:
            continue
        for n in ast.walk(arv):
            if not isinstance(n, ast.ImportFrom):
                continue
            if n.level > 0:
                pkg = r.split("/")[:-1]
                pkg = pkg[:len(pkg) - (n.level - 1)] if n.level > 1 else pkg
                modulo = ".".join(pkg + ([n.module] if n.module else []))
            else:
                modulo = n.module or ""
            alvo = mapa.get(modulo)
            if not alvo:
                continue
            d = defs(alvo)
            if d is None:
                continue
            for a in n.names:
                if a.name != "*" and a.name not in d and f"{modulo}.{a.name}" not in mapa:
                    problemas.append((r, alvo,
                        f"{r} faz 'from {modulo} import {a.name}', mas {alvo} não define '{a.name}'."))
    return problemas


def write_requirements(p) -> list[str]:
    mapa = _mapa_modulos(p)
    locais = {r.split("/")[0].removesuffix(".py") for r in p.tree()}
    externos = set()
    for r in (r for r in p.tree() if r.endswith(".py")):
        try:
            arv = ast.parse(p.read_file(r))
        except SyntaxError:
            continue
        for n in ast.walk(arv):
            nomes = []
            if isinstance(n, ast.Import):
                nomes = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                nomes = [n.module.split(".")[0]]
            for nome in nomes:
                if nome not in sys.stdlib_module_names and nome not in locais and nome not in mapa:
                    externos.add(ALIAS_PIP.get(nome, nome))
    existente = p.read_file("requirements.txt").lower()
    novos = sorted(x for x in externos if x.lower() not in existente)
    if novos:
        p.write_file("requirements.txt", (p.read_file("requirements.txt").rstrip("\n") + "\n"
                     if existente.strip() else "") + "\n".join(novos) + "\n")
    return novos


def signatures(p, excluir: str = "") -> str:
    partes = []
    for rel in p.tree():
        if rel == excluir or not eh_codigo(rel) or Path(rel).suffix in {".css", ".html"}:
            continue
        linhas = [l.rstrip() for l in p.read_file(rel, 20000).splitlines() if SIG_RE.match(l)]
        if linhas:
            partes.append(f"# {rel}\n" + "\n".join(linhas[:40]))
    return "\n\n".join(partes)


def python_exe(p) -> str:
    venv = p.root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(venv) if venv.exists() else sys.executable


def adapt_cmd(p, cmd: str) -> str:
    return re.sub(r"^python3?\s", lambda m: f'"{python_exe(p)}" ', cmd.strip())


def _s(x) -> str:
    return x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "")


def run(cmd: str, cwd, timeout: int = 120) -> dict:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONPATH=str(cwd))
    try:
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=env)
        out = (r.stdout or "") + (f"\n[stderr]\n{r.stderr}" if r.stderr else "")
        return {"ok": r.returncode == 0, "code": r.returncode, "out": out.strip()}
    except subprocess.TimeoutExpired as e:
        return {"ok": None, "code": None,
                "out": f"⏱ Terminou por timeout ({timeout}s).\n{_s(e.stdout)}\n{_s(e.stderr)}".strip()}


def setup_env(p) -> str:
    venv = p.root / ".venv"
    saida = []
    if not venv.exists():
        r = subprocess.run([sys.executable, "-m", "venv", str(venv)],
                           capture_output=True, text=True)
        saida.append(r.stdout + r.stderr)
    if p.exists("requirements.txt"):
        r = run(f'"{python_exe(p)}" -m pip install -r requirements.txt', p.code, 600)
        saida.append(r["out"])
    return "\n".join(saida).strip() or "Ambiente pronto."


def traceback_files(saida: str, p) -> list[str]:
    encontrados = []
    for caminho in re.findall(r'File "([^"]+)", line \d+', saida):
        try:
            rel = Path(caminho).resolve().relative_to(p.code.resolve()).as_posix()
            if rel not in encontrados:
                encontrados.append(rel)
        except Exception:
            pass
    encontrados = encontrados[::-1]  # frames mais fundos primeiro
    if not encontrados:  # outras linguagens: ficheiros mencionados no output
        encontrados = [r for r in p.tree() if eh_codigo(r) and Path(r).name in saida]
    return encontrados[:3]