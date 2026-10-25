import re

FENCE = re.compile(r"```[^\n`]*\n(.*?)(?:```|\Z)", re.S)
MULTI = re.compile(
    r"^[#*\s]*FILE\s*:\s*`?([^\s`*]+)`?[*\s]*\n+```[^\n`]*\n(.*?)(?:\n```|\Z)",
    re.S | re.I | re.M)
LINHA = re.compile(
    r"^[\W_]*(EDIT|FILE)\s*:\s*`?([^\s|`]+)`?[ \t]*(?:\|([^|\n]*))?"
    r"(?:\|[ \t]*deps?\s*:\s*([^\n]*))?", re.I | re.M)
RUN = re.compile(r"^[\W_]*RUN\s*:\s*`?(.+?)`?\s*$", re.I | re.M)


def safe_rel(p: str) -> str:
    """Caminho relativo seguro (sem sair da pasta do projeto)."""
    p = p.replace("\\", "/").strip().strip("`'\"")
    while p.startswith("./"):
        p = p[2:]
    if (not p or p.startswith("/") or re.match(r"^[A-Za-z]:", p)
            or ".." in p.split("/") or p.endswith("/")):
        raise ValueError(f"caminho inválido: {p!r}")
    return p


def extract_code(texto: str) -> str:
    blocos = FENCE.findall(texto)
    if blocos:
        return max(blocos, key=len).strip("\n") + "\n"
    return texto.strip() + "\n"


def strip_outer_fence(texto: str) -> str:
    t = texto.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[^\n]*\n", "", t)
        t = re.sub(r"\n```\s*$", "", t)
    return t.strip() + "\n"


def multi_files(texto: str) -> list[tuple[str, str]]:
    saida = []
    for caminho, codigo in MULTI.findall(texto):
        try:
            saida.append((safe_rel(caminho), codigo.strip("\n") + "\n"))
        except ValueError:
            continue
    return saida


def parse_linhas(texto: str) -> list[dict]:
    itens, vistos = [], set()
    for tipo, caminho, desc, deps in LINHA.findall(texto):
        try:
            caminho = safe_rel(caminho)
        except ValueError:
            continue
        if caminho in vistos:
            continue
        vistos.add(caminho)
        lista = []
        for d in (deps or "").split(","):
            try:
                if d.strip():
                    lista.append(safe_rel(d))
            except ValueError:
                pass
        itens.append({"tipo": tipo.upper(), "path": caminho,
                      "desc": (desc or "").strip(), "deps": lista})
    return itens


def parse_run(texto: str) -> str:
    m = RUN.search(texto)
    return m.group(1).strip() if m else ""