"""Tests for app.py — run with: python3 -m unittest -v

Uses only the Python standard library. Starts the real app on a
free local port in a thread, so the tests check the actual HTTP
behaviour, not a copy of the logic.
"""

import json
import os
import socket
import struct
import threading
import unittest
import urllib.request
from http.server import HTTPServer

import app as app_module


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _PostgresStub(threading.Thread):
    """Answers a Postgres startup message with an auth request ('R').

    Enough for app.py's /health check to report "postgres".
    """

    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]

    def run(self):
        conn, _ = self.sock.accept()
        with conn:
            conn.recv(1024)
            # 'R' + length 8 + auth code 0 (AuthenticationOk)
            conn.sendall(b"R" + struct.pack("!I", 8) + struct.pack("!I", 0))


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = _free_port()
        cls.server = HTTPServer(("127.0.0.1", cls.port), app_module.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as r:
            return r.status, r.read().decode()

    def test_root_returns_day_message(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Docker refresh", body)

    def test_health_without_database_is_unreachable(self):
        # DB_HOST points at a closed port, so no Postgres answers.
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = str(_free_port())
        status, body = self._get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["db"], "unreachable")

    def test_health_with_postgres_stub_is_postgres(self):
        stub = _PostgresStub()
        stub.start()
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = str(stub.port)
        status, body = self._get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["db"], "postgres")
        stub.sock.close()


if __name__ == "__main__":
    unittest.main()
