"""Cube de mentira: serve as respostas gravadas do Cube real (`testdata/`).

Os testes das ferramentas MCP precisam de um Cube previsível e offline. Este stub
responde `/meta` e `/load` com o que foi gravado do Cube real (ver `mcp/README.md`
para regravar). Um `/load` sem resposta gravada devolve 404 na mesma estrutura de
erro do Cube, para que um teste nunca passe por acidente.
"""

from __future__ import annotations

import json
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

TESTDATA = pathlib.Path(__file__).resolve().parent.parent / "testdata"


def _read(name: str) -> dict[str, Any]:
    return json.loads((TESTDATA / name).read_text())


def recorded_fixtures() -> dict[str, dict[str, Any]]:
    """Respostas gravadas de `/load`, por nome de arquivo."""
    return {path.name: _read(path.name) for path in sorted(TESTDATA.glob("load_*.json"))}


def normalized(query: dict[str, Any]) -> dict[str, Any]:
    """A pergunta governada reduzida ao que importa: medidas, dimensões, filtros, limite."""
    return {
        "measures": sorted(query.get("measures", [])),
        "dimensions": sorted(query.get("dimensions", [])),
        "filters": query.get("filters", []),
        "limit": query.get("limit", query.get("rowLimit")),
    }


class FakeCube:
    """Stub HTTP do Cube Core, sobre as respostas gravadas.

    Uso::

        with FakeCube() as cube:
            ...  # cube.url aponta para o stub; cube.load_queries guarda o que foi pedido
    """

    def __init__(self) -> None:
        self.meta: dict[str, Any] = _read("meta.json")
        self.fixtures = recorded_fixtures()
        self.load_queries: list[dict[str, Any]] = []
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._httpd.daemon_threads = True
        self._httpd.stub = self  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}"

    def fixture_named(self, name: str) -> dict[str, Any]:
        """A resposta gravada daquele arquivo (o teste conhece o que ele mesmo pede)."""
        return self.fixtures[name]

    def fixture_for(self, query: dict[str, Any]) -> dict[str, Any] | None:
        """A resposta gravada para esta pergunta governada, se existir."""
        wanted = normalized(query)
        for fixture in self.fixtures.values():
            if normalized(fixture["query"]) == wanted:
                return fixture
        return None

    def __enter__(self) -> FakeCube:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 (nome exigido pelo http.server)
        route = urlparse(self.path)
        stub: FakeCube = self.server.stub  # type: ignore[attr-defined]
        if route.path.endswith("/meta"):
            self._respond(200, stub.meta)
        elif route.path.endswith("/load"):
            query = json.loads(parse_qs(route.query)["query"][0])
            stub.load_queries.append(query)
            fixture = stub.fixture_for(query)
            if fixture is None:
                self._respond(404, {"error": f"nenhuma resposta gravada para {normalized(query)}"})
            else:
                self._respond(200, fixture)
        else:
            self._respond(404, {"error": f"rota desconhecida: {route.path}"})

    def _respond(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Silencia o log padrão do `http.server` (o teste já falha alto quando precisa)."""
