"""Cliente mínimo da REST API do Cube Core.

Só o que o agente precisa: ler o catálogo de medidas/dimensões (`/meta`) e
consultar (`/load`). Sem dependências além da stdlib — o SDK do MCP é a única
dependência do servidor.

O Cube roda em `CUBEJS_DEV_MODE=true` (ver `cube/.env`), então a REST API não
exige token; a SQL API é que tem credenciais explícitas.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "http://localhost:4000"
API_PREFIX = "/cubejs-api/v1"


class CubeError(RuntimeError):
    """Erro ao falar com o Cube (HTTP, payload ou catálogo)."""


class CubeClient:
    """Acesso HTTP à REST API do Cube (`/cubejs-api/v1`)."""

    def __init__(self, base_url: str | None = None, timeout: float = 60.0) -> None:
        self.base_url = (base_url or os.environ.get("CUBE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = f"{self.base_url}{API_PREFIX}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as error:
            body = error.read().decode(errors="replace")
            raise CubeError(f"HTTP {error.code} em {url}: {body}") from error
        except urllib.error.URLError as error:
            raise CubeError(f"não foi possível falar com o Cube em {self.base_url}: {error.reason}") from error
        if isinstance(payload, dict) and "error" in payload:
            raise CubeError(str(payload["error"]))
        return payload

    def meta(self) -> dict[str, Any]:
        """Catálogo do Cube: cubos/views com suas medidas e dimensões."""
        return self._get("/meta")

    def load(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Executa uma consulta e devolve as linhas cruas de `/load`."""
        return self._get("/load", {"query": json.dumps(query)}).get("data", [])


def _model(meta: dict[str, Any], name: str) -> dict[str, Any]:
    for cube in meta.get("cubes", []):
        if cube["name"] == name:
            return cube
    available = ", ".join(cube["name"] for cube in meta.get("cubes", []))
    raise CubeError(f"modelo '{name}' não existe no Cube; disponíveis: {available}")


def _members(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": entry["name"], "type": entry["type"], "description": entry.get("description", "")}
        for entry in entries
        if entry.get("isVisible", True)
    ]


def measures_of(meta: dict[str, Any], model: str) -> list[dict[str, Any]]:
    """Medidas governadas do modelo (nome, tipo, descrição)."""
    return _members(_model(meta, model)["measures"])


def dimensions_of(meta: dict[str, Any], model: str) -> list[dict[str, Any]]:
    """Dimensões governadas do modelo (nome, tipo, descrição)."""
    return _members(_model(meta, model)["dimensions"])


def table(columns: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Achata as linhas do Cube (`{membro: valor}`) numa tabela colunar."""
    return {
        "columns": columns,
        "rows": [[row.get(column) for column in columns] for row in rows],
        "row_count": len(rows),
    }
