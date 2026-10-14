"""Demo do agente sobre a camada semântica, pelo MCP.

Sobe o servidor MCP (`server.py`) como processo filho e fala com ele pelo
protocolo (stdio) — o mesmo caminho de um cliente MCP de verdade (o trecho de
configuração do cliente está no `README.md`).

O "agente" aqui é um roteiro fixo, **sem LLM**: ele descobre as medidas e
dimensões governadas, confere que o plano do roteiro existe nesse catálogo e só
então consulta. É exatamente o que interessa mostrar em aula — o agente não
escreve SQL, ele escolhe membros governados; e o número vem da mesma definição
que o Superset usa.

    mcp/.venv/bin/python mcp/demo.py [pergunta]

(ou `make mcp-demo`) — sem argumento, roda a primeira pergunta do roteiro.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import Any

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER = pathlib.Path(__file__).resolve().parent / "server.py"
MODEL = os.environ.get("CUBE_MODEL", "titles_overview")  # a mesma variável que o servidor lê


def member(name: str) -> str:
    """O membro como o catálogo o nomeia (o Cube qualifica com o modelo)."""
    return f"{MODEL}.{name}"


# O roteiro: pergunta de negócio → plano em membros governados. Um agente com
# LLM descobriria esse plano sozinho a partir de `list_measures`/`list_dimensions`.
QUESTIONS: dict[str, dict[str, Any]] = {
    "Qual país tem a melhor nota média entre os que têm pelo menos 20 títulos?": {
        "measures": [member("count_titles"), member("avg_rating")],
        "dimensions": [member("country")],
        "filters": [
            # `set` = país conhecido: o join da ponte preserva os títulos sem país
            # numa linha NULL, que não é um país (ver `cube/README.md`).
            {"member": member("country"), "operator": "set"},
            {"member": member("count_titles"), "operator": "gte", "values": ["20"]},
        ],
        "limit": 1000,
        "rank_by": member("avg_rating"),
    },
    "Quantos títulos e qual a nota média, por gênero?": {
        "measures": [member("count_titles"), member("avg_rating")],
        "dimensions": [member("genre")],
        "limit": 1000,
        "rank_by": None,
    },
}


def _parameters() -> StdioServerParameters:
    """O transporte stdio não herda o ambiente; repassamos o que o servidor usa."""
    env = {name: os.environ[name] for name in ("CUBE_URL", "CUBE_MODEL") if name in os.environ}
    return StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)


def _names(catalog: list[dict[str, Any]]) -> list[str]:
    return [member["name"] for member in catalog]


def _column(columns: list[str], member: str) -> str:
    """A coluna do membro (o Cube a devolve qualificada com o modelo)."""
    short = member.rsplit(".", 1)[-1]
    for column in columns:
        if column.rsplit(".", 1)[-1] == short:
            return column
    raise LookupError(f"a consulta não devolveu a coluna de {member}: {', '.join(columns)}")


def _print_table(columns: list[str], rows: list[list[Any]], indent: str = "      ") -> None:
    headers = [column.rsplit(".", 1)[-1] for column in columns]
    widths = [max([len(header)] + [len(str(row[index])) for row in rows]) for index, header in enumerate(headers)]
    print(indent + "  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    for row in rows:
        print(indent + "  ".join(str(value).ljust(width) for value, width in zip(row, widths)))


def _plan_members(plan: dict[str, Any]) -> list[str]:
    return plan["measures"] + plan["dimensions"]


async def _discover(session: ClientSession) -> set[str]:
    """O agente pergunta o que existe antes de escolher o que consultar."""
    measures = (await session.call_tool("list_measures", {})).structured_content["measures"]
    dimensions = (await session.call_tool("list_dimensions", {})).structured_content["dimensions"]
    print(f"[1] list_measures()    → {', '.join(_names(measures))}")
    print(f"[2] list_dimensions()  → {', '.join(_names(dimensions))}")
    return set(_names(measures)) | set(_names(dimensions))


def run(question: str) -> int:
    plan = QUESTIONS[question]
    print(f"Pergunta: {question}\n")

    async def demo() -> int:
        async with stdio_client(_parameters()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                known = await _discover(session)

                invented = [member for member in _plan_members(plan) if member not in known]
                if invented:
                    print(f"\nFora da camada governada: {', '.join(invented)}. Governados: {', '.join(sorted(known))}")
                    return 1

                arguments = {name: value for name, value in plan.items() if name != "rank_by"}
                result = await session.call_tool("query", arguments)
                if result.is_error:
                    print(f"\nA consulta governada falhou: {result.content[0].text}")
                    return 1

                print("[3] query(...)         → chamada governada do agente:")
                print("\n".join(f"      {line}" for line in json.dumps(arguments, indent=2, ensure_ascii=False).splitlines()))

                table = result.structured_content
                columns, rows = table["columns"], table["rows"]
                print(f"\n      {table['row_count']} linhas devolvidas pelo Cube\n")

                rank_by = plan["rank_by"]
                if rank_by is None:
                    _print_table(columns, rows)
                    return 0

                # O contrato governado é medidas × dimensões (+ filtros, limite):
                # ranking é apresentação, então ordenamos aqui, na ordem da medida.
                index = columns.index(_column(columns, rank_by))
                ordered = sorted(rows, key=lambda row: float(row[index]), reverse=True)
                _print_table(columns, ordered[:5])
                top = ordered[0]
                print(
                    f"\nResposta: {top[columns.index(_column(columns, plan['dimensions'][0]))]} — "
                    f"nota média {float(top[index]):.3f} em "
                    f"{int(top[columns.index(_column(columns, 'count_titles'))])} títulos."
                )
                return 0

    return anyio.run(demo)


def _question(argv: list[str]) -> str:
    if not argv:
        return next(iter(QUESTIONS))
    wanted = " ".join(argv).lower()
    for question in QUESTIONS:
        if wanted in question.lower():
            return question
    raise SystemExit("pergunta fora do roteiro do demo. Opções:\n  - " + "\n  - ".join(QUESTIONS))


if __name__ == "__main__":
    sys.exit(run(_question(sys.argv[1:])))
