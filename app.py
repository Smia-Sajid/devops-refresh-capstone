"""Day 2 starter app — Smi's DevOps refresh.

Same tiny web app as Day 1, still only the Python standard library, so
there is still nothing to `pip install`.

Day 2 adds one new endpoint so Compose can prove the app and the
database are wired together without needing a Postgres driver:

  GET /        -> "Hello from Smi's Docker refresh - Day 6 is running!"
  (Day 6 changes only this message, so a rolling update is visible:
  Day 2 message = old version, Day 6 message = new version.)
  GET /health  -> JSON: {"status": "ok", "db": "postgres"|"unreachable", ...}

The /health check speaks a little of the Postgres wire protocol: it
opens a connection and sends a Postgres startup message (user/database
from POSTGRES_USER / POSTGRES_DB). If the other end answers with a real
Postgres message, the database is Postgres. A bare TCP connect was not
enough — proxies and firewalls can accept a TCP connection without any
database behind it. The check stops before login, so the app never
needs the database password.

Run it directly with `python3 app.py`, or with Compose:
`docker compose up` — then visit http://localhost:8000/health
"""
import json
import os
import socket
import struct
from http.server import BaseHTTPRequestHandler, HTTPServer


def _recv_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            break
        data += chunk
    return data


def db_status(host, port, user, database, timeout=3.0):
    """'postgres' if the other end answers like Postgres, else 'unreachable'.

    Sends a Postgres startup message and reads the first reply message.
    A Postgres server answers with 'R' (auth request), 'E' (error, e.g.
    unknown user/database), 'S'/'K'/'Z' (parameter status / ready) — any
    of those proves it is Postgres. Anything else, a timeout, or a
    refused connection means no Postgres is answering there.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            params = (
                b"user\x00" + user.encode() + b"\x00"
                b"database\x00" + database.encode() + b"\x00\x00"
            )
            startup = struct.pack("!I", len(params) + 8) + struct.pack("!I", 196608) + params
            sock.sendall(startup)
            header = _recv_exact(sock, 5)
            if len(header) < 5:
                return "unreachable"
            return "postgres" if header[:1] in b"RESKZ" else "unreachable"
    except OSError:
        return "unreachable"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            host = os.environ.get("DB_HOST", "db")
            port = int(os.environ.get("DB_PORT", "5432"))
            payload = {
                "status": "ok",
                "db": db_status(
                    host, port,
                    os.environ.get("POSTGRES_USER", "smi"),
                    os.environ.get("POSTGRES_DB", "myapp"),
                ),
                "db_host": host,
                "db_port": port,
            }
            body = (json.dumps(payload) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        else:
            body = b"Hello from Smi's Docker refresh - Day 6 is running!\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the terminal output clean
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
