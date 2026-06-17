import subprocess
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, send_file

VITIMAS = [f"vitima_{n:02d}" for n in range(1, 26)]


def estado(v: str) -> tuple[str, str]:
    try:
        r = subprocess.run(["docker", "exec", v, "cat", "/app/infectado.txt"],
                           capture_output=True, text=True, timeout=2)
        return v, r.stdout.strip()
    except Exception:
        return v, "?"


def coletar() -> dict[str, str]:
    with ThreadPoolExecutor(max_workers=25) as ex:
        return dict(ex.map(estado, VITIMAS))


app = Flask(__name__)


@app.get("/status")
def status():
    return jsonify(coletar())


@app.get("/")
def index():
    return send_file("monitor.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
