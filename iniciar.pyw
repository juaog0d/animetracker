import http.server
import json
import os
import shutil
import subprocess
import threading
import webbrowser
from pathlib import Path

# ── Configuração ──────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / "config.json"
BASE_DIR    = Path(__file__).parent   # pasta onde está o iniciar.pyw
PORT        = 7411

# ── Helpers ───────────────────────────────────────────────────
def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def run_git(*args):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(BASE_DIR),
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stdout + result.stderr

# ── Handler HTTP ──────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, *a):
        pass  # silencia logs no terminal

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self.send_json(200, {"ok": True})

        elif self.path == "/config":
            self.send_json(200, load_config())

        else:
            self.send_json(404, {"erro": "rota não encontrada"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length) or b"{}")

        # ── Salvar configuração ───────────────────────────────
        if self.path == "/salvar-config":
            save_config(body)
            self.send_json(200, {"ok": True})

        # ── Importar JSON dos Downloads ───────────────────────
        elif self.path == "/importar":
            cfg = load_config()
            destino = BASE_DIR / "animes.json"

            # Aceita tanto string única (legado) quanto lista de caminhos
            raw_downloads = cfg.get("downloads", [])
            if isinstance(raw_downloads, str):
                raw_downloads = [raw_downloads]

            origem = None
            for dl_path in raw_downloads:
                pasta = Path(dl_path).expanduser()
                if not pasta.exists():
                    continue
                candidatos = sorted(
                    pasta.glob("animes*.json"),
                    key=lambda f: f.stat().st_mtime,
                    reverse=True
                )
                if candidatos:
                    origem = candidatos[0]
                    break

            if origem is None:
                self.send_json(200, {"ok": False, "msg": "Nenhum arquivo animes*.json encontrado em nenhuma das pastas configuradas."})
                return

            shutil.copy2(str(origem), str(destino))
            self.send_json(200, {"ok": True, "msg": f"✓ '{origem.name}' copiado para a pasta do projeto."})

        # ── Git: pull (atualizar) ─────────────────────────────
        elif self.path == "/pull":
            ok, log = run_git("pull", "--rebase", "origin", "main")
            if ok:
                self.send_json(200, {"ok": True,  "msg": "✓ Repositório atualizado com sucesso!"})
            else:
                self.send_json(200, {"ok": False, "msg": f"Erro no git pull:\n{log}"})

        # ── Git: push (enviar) ────────────────────────────────
        elif self.path == "/push":
            run_git("add", ".")
            run_git("commit", "-m", "atualizado")
            ok_pull, log_pull = run_git("pull", "--rebase", "origin", "main")
            ok_push, log_push = run_git("push")
            if ok_push:
                self.send_json(200, {"ok": True,  "msg": "✓ Dados enviados para o GitHub!"})
            else:
                self.send_json(200, {"ok": False, "msg": f"Erro no git push:\n{log_pull}\n{log_push}"})

        else:
            self.send_json(404, {"erro": "rota não encontrada"})


# ── Iniciar servidor + abrir navegador ───────────────────────
def iniciar_servidor():
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()

if __name__ == "__main__":
    t = threading.Thread(target=iniciar_servidor, daemon=True)
    t.start()
    webbrowser.open(f"file:///{BASE_DIR / 'index.html'}")
    # mantém o processo vivo
    t.join()
