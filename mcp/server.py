"""Servidor MCP mínimo sobre a camada semântica do Cube.

Três ferramentas — o agente *descobre* o que existe e consulta o que é
governado, em vez de escrever SQL livre (é o ponto de *context engineering*):

  - list_measures   → {"measures": [{name, type, description}]}
  - list_dimensions → {"dimensions": [{name, type, description}]}
  - query           → {"columns": [...], "rows": [[...]], "row_count": N}

As ferramentas devolvem **objetos** (e não listas soltas) para o agente ler um
contrato explícito, igual nas três: o que veio é o que está escrito na chave.

Fala com o Cube pela REST API (`/meta`, `/load`). Por padrão enxerga só a view
`titles_overview` — a fachada plana do modelo — para que o agente não precise
conhecer os cubos internos nem os joins. `CUBE_MODEL`/`CUBE_URL` mudam isso.

Membro fora do catálogo vira `ToolError`: a mensagem (com os membros válidos)
chega ao modelo num resultado `is_error`, que é como ele se corrige sozinho.
Falha de infraestrutura (Cube fora do ar) continua sendo crash — aparece no log
do servidor, não no contexto do agente.

Rodar (stdio, o transporte que os clientes MCP usam):

    python server.py
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from cube import CubeClient, dimensions_of, measures_of, table

MODEL = os.environ.get("CUBE_MODEL", "titles_overview")
client = CubeClient()

server = MCPServer(
    "camada-semantica",
    instructions=(
        "Camada semântica governada de títulos (Cube). Descubra as medidas e "
        "dimensões com list_measures/list_dimensions e consulte com query. "
        "Não invente métricas: use só o que o catálogo expõe."
    ),
)


def _qualify(member: str) -> str:
    """Aceita `avg_rating` ou `titles_overview.avg_rating` e devolve o nome completo."""
    return member if "." in member else f"{MODEL}.{member}"


def _governed_members() -> set[str]:
    """Membros que o modelo governado expõe (o que o agente pode pedir)."""
    catalog = client.meta()
    known = {member["name"] for member in measures_of(catalog, MODEL)}
    known |= {member["name"] for member in dimensions_of(catalog, MODEL)}
    return known


def _qualified(members: list[str], known: set[str], kind: str) -> list[str]:
    """Qualifica e valida uma lista de membros contra o catálogo governado."""
    qualified = [_qualify(member) for member in members]
    unknown = [member for member in qualified if member not in known]
    if unknown:
        raise ToolError(
            f"{kind} fora da camada governada: {', '.join(unknown)}. "
            f"Membros disponíveis: {', '.join(sorted(known))}."
        )
    return qualified


def _governed_filters(filters: list[dict[str, Any]], known: set[str]) -> list[dict[str, Any]]:
    """Valida o membro de cada filtro; filtros compostos ficam de fora."""
    governed = []
    for condition in filters:
        if "member" not in condition:
            raise ToolError(
                "filtros compostos (and/or) não são suportados: use filtros simples "
                "no formato {\"member\": ..., \"operator\": ..., \"values\": [...]}."
            )
        governed.append({**condition, "member": _qualified([condition["member"]], known, "filtro")[0]})
    return governed


@server.tool(
    description=(
        "Lista as medidas governadas da camada semântica: um objeto {\"measures\": "
        "[{name, type, description}]}. Use os nomes retornados em `query` — não "
        "invente métricas."
    )
)
def list_measures() -> dict[str, Any]:
    return {"measures": measures_of(client.meta(), MODEL)}


@server.tool(
    description=(
        "Lista as dimensões governadas: um objeto {\"dimensions\": "
        "[{name, type, description}]}. Qualquer dimensão pode fatiar qualquer medida "
        "do catálogo."
    )
)
def list_dimensions() -> dict[str, Any]:
    return {"dimensions": dimensions_of(client.meta(), MODEL)}


@server.tool(
    description=(
        "Consulta a camada semântica: medidas × dimensões, com filtros opcionais "
        "(formato do Cube: {member, operator, values}) e limite. Devolve uma tabela "
        "{columns, rows, row_count}. Só aceita membros do catálogo governado."
    )
)
def query(
    measures: list[str],
    dimensions: list[str] | None = None,
    filters: list[dict[str, Any]] | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    if not measures:
        raise ToolError("informe ao menos uma medida.")
    known = _governed_members()
    qualified_measures = _qualified(measures, known, "medida")
    qualified_dimensions = _qualified(dimensions or [], known, "dimensão")
    rows = client.load(
        {
            "measures": qualified_measures,
            "dimensions": qualified_dimensions,
            "filters": _governed_filters(filters or [], known),
            "limit": limit,
        }
    )
    # Colunas na ordem em que a tabela se lê: primeiro as dimensões, depois as medidas.
    return table(qualified_dimensions + qualified_measures, rows)


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
