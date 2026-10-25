import json
import requests
import config


def is_up() -> bool:
    try:
        return requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=2).ok
    except requests.RequestException:
        return False


def list_models() -> list[str]:
    try:
        r = requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=3)
        return sorted(m["name"] for m in r.json().get("models", []))
    except Exception:
        return []


def chat(system, user, model=None, num_ctx=None, temperature=None,
         on_token=None, tentativas=2) -> str:
    payload = {
        "model": model or config.DEFAULT_MODEL,
        "stream": True,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {
            "num_ctx": num_ctx or config.DEFAULT_NUM_CTX,
            "temperature": config.TEMPERATURE if temperature is None else temperature,
            "num_predict": 4096,
            "repeat_penalty": 1.15,
        },
    }
    for _ in range(tentativas):
        try:
            partes = []
            with requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload,
                               stream=True, timeout=(10, 900)) as r:
                r.raise_for_status()
                for linha in r.iter_lines():
                    if not linha:
                        continue
                    d = json.loads(linha)
                    if "error" in d:
                        raise RuntimeError(d["error"])
                    tok = d.get("message", {}).get("content", "")
                    if tok:
                        partes.append(tok)
                        if on_token:
                            on_token(tok)
                        texto_atual = "".join(partes)
                        if len(texto_atual) > 2000:
                            cauda = texto_atual[-800:]
                            metade = cauda[:400]
                            if metade and texto_atual.count(metade) >= 3:
                                break
                    if d.get("done"):
                        break
            texto = "".join(partes).strip()
            if texto:
                return texto
        except requests.ConnectionError:
            raise RuntimeError("Ollama não está a correr. Abre outra CMD e executa: ollama serve")
    raise RuntimeError("O modelo devolveu uma resposta vazia.")