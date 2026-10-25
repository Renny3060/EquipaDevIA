import json
import os
import re
import threading
import time
from pathlib import Path

from config import PROJECTS_DIR

IGNORAR = {"__pycache__", ".git", "node_modules", ".venv", "venv",
           ".pytest_cache", "dist", "build"}
_lock = threading.Lock()


def slug(nome: str) -> str:
    return re.sub(r"[^\w\-]+", "_", nome.strip()).strip("_") or "projeto"


def list_projects() -> list[str]:
    PROJECTS_DIR.mkdir(exist_ok=True)
    return sorted(d.name for d in PROJECTS_DIR.iterdir() if (d / ".fabrica").is_dir())


class Project:
    def __init__(self, nome: str):
        self.name = slug(nome)
        self.root = PROJECTS_DIR / self.name
        self.code = self.root / "codigo"
        self.meta = self.root / ".fabrica"
        self.code.mkdir(parents=True, exist_ok=True)
        self.meta.mkdir(exist_ok=True)
        self.state_file = self.meta / "estado.json"
        self.log_file = self.meta / "log.jsonl"
        self.state = self._load()

    def _load(self) -> dict:
        base = {"prompt": "", "language": "Python", "status": "novo",
                "requirements": "", "plan": [], "contract": "", "run_cmd": "",
                "test_cmd": "", "historico": [], "relatorio": "",
                "criado": time.strftime("%Y-%m-%d %H:%M")}
        if self.state_file.exists():
            try:
                base.update(json.loads(self.state_file.read_text(encoding="utf-8")))
            except Exception:
                pass
        return base

    def save(self):
        with _lock:
            self.state_file.write_text(
                json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def log(self, kind: str, msg: str, agent: str = ""):
        ev = {"t": time.strftime("%H:%M:%S"), "kind": kind, "agent": agent, "msg": msg}
        with _lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    def read_log(self, n: int = 300) -> list[dict]:
        if not self.log_file.exists():
            return []
        with _lock:
            linhas = self.log_file.read_text(encoding="utf-8").splitlines()[-n:]
        out = []
        for l in linhas:
            try:
                out.append(json.loads(l))
            except Exception:
                pass
        return out

    def tree(self) -> list[str]:
        saida = []
        for pasta, dirs, ficheiros in os.walk(self.code):
            dirs[:] = [d for d in dirs if d not in IGNORAR]
            for f in ficheiros:
                rel = Path(pasta, f).relative_to(self.code).as_posix()
                saida.append(rel)
        return sorted(saida)

    def exists(self, rel: str) -> bool:
        return (self.code / rel).is_file()

    def read_file(self, rel: str, limit: int | None = None) -> str:
        try:
            t = (self.code / rel).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
        return t[:limit] if limit else t

    def write_file(self, rel: str, content: str):
        destino = (self.code / rel).resolve()
        if self.code.resolve() not in destino.parents:
            raise ValueError(f"fora da pasta do projeto: {rel}")
        if destino.exists():
            antigo = destino.read_text(encoding="utf-8", errors="replace")
            if antigo != content:
                bk = self.meta / "versoes" / time.strftime("%Y%m%d-%H%M%S") / rel
                bk.parent.mkdir(parents=True, exist_ok=True)
                bk.write_text(antigo, encoding="utf-8")
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(content, encoding="utf-8")
        if rel.startswith("tests/") and rel.endswith(".py"):
            init = self.code / "tests" / "__init__.py"
            if not init.exists():
                init.write_text("", encoding="utf-8")