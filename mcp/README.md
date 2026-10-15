# Agente — servidor MCP sobre a camada semântica

Servidor MCP mínimo que expõe a camada semântica do Cube como ferramentas para um
agente de IA. O agente **descobre** o que é governado (`list_measures`,
`list_dimensions`) e consulta (`query`) — não escreve SQL livre. É o *context
engineering* da aula: o vocabulário do agente é o modelo semântico, não o catálogo
do Trino.

Por que um servidor próprio: o Cube self-hosted não tem MCP oficial utilizável (o
oficial é atrelado ao Cube Cloud). Aqui a interface do agente é a REST API do Cube
(`/cubejs-api/v1/meta` e `/load`).

## Ferramentas

| Ferramenta | Argumentos | Devolve |
| - | - | - |
| `list_measures` | — | `{"measures": [{name, type, description}]}` |
| `list_dimensions` | — | `{"dimensions": [{name, type, description}]}` |
| `query` | `measures[]` (obrigatório), `dimensions[]`, `filters[]`, `limit` | `{"columns": [...], "rows": [[...]], "row_count": N}` |

`filters` segue o formato do Cube: `{"member": ..., "operator": ..., "values": [...]}`.
Membro fora do catálogo vira erro (`is_error`) com a lista do que existe — o agente
se corrige lendo a mensagem — e **nada disso chega ao Cube**. O servidor qualifica
nomes curtos (`avg_rating` → `titles_overview.avg_rating`) e enxerga só a view
`titles_overview`, a fachada plana: o agente não precisa conhecer os cubos internos
nem os joins.

## Rodar

O servidor fala com o Cube em `http://localhost:4000` (`CUBE_URL` e `CUBE_MODEL`
mudam isso). O Cube sobe com o stack:

```bash
docker compose up -d
make mcp-install        # cria mcp/.venv e instala o SDK do MCP
make mcp-demo
```

## Cliente MCP

O transporte é stdio: qualquer cliente MCP aponta para o `server.py` desta pasta.
O repo já traz a entrada pronta num `.mcp.json` na raiz (config de escopo de projeto,
com caminhos relativos à própria raiz), então cliente que lê config de projeto
encontra o servidor sozinho — inclusive pedindo aprovação na primeira vez, se for o
caso. Cliente que não lê config de projeto, ou que quer o servidor em todos os
projetos, copia o trecho ajustando os caminhos:

```json
{
  "mcpServers": {
    "camada-semantica": {
      "command": "/caminho/para/o/repo/mcp/.venv/bin/python",
      "args": ["/caminho/para/o/repo/mcp/server.py"],
      "env": { "CUBE_URL": "http://localhost:4000" }
    }
  }
}
```

`CUBE_URL` no `.mcp.json` do repo é `${CUBE_URL:-http://localhost:4000}` — exportado
no shell, o valor do ambiente vence o default.

Com o cliente ligado, pergunte em português (*"qual país tem a melhor nota média?"*):
o modelo chama as ferramentas e a resposta vem da mesma definição que o Superset usa.

## Demo

`make mcp-demo` roda o roteiro de perguntas. O "agente" é fixo, **sem LLM**: o que
se demonstra é o loop *descoberta → chamada governada → resposta*.

```
Pergunta: Qual país tem a melhor nota média entre os que têm pelo menos 20 títulos?

[1] list_measures()    → titles_overview.count_titles, titles_overview.avg_rating, titles_overview.total_votes
[2] list_dimensions()  → titles_overview.release_year, titles_overview.title_type, titles_overview.genre, titles_overview.country
[3] query(...)         → chamada governada do agente:
      {
        "measures": [
          "titles_overview.count_titles",
          "titles_overview.avg_rating"
        ],
        "dimensions": [
          "titles_overview.country"
        ],
        "filters": [
          {
            "member": "titles_overview.country",
            "operator": "set"
          },
          {
            "member": "titles_overview.count_titles",
            "operator": "gte",
            "values": [
              "20"
            ]
          }
        ],
        "limit": 1000
      }

      15 linhas devolvidas pelo Cube

      country         count_titles  avg_rating
      Japan           29            7.0793103448275865
      Germany         92            7.073333333333333
      Mexico          22            6.99
      Spain           27            6.868181818181819
      United Kingdom  309           6.841549295774649

Resposta: Japan — nota média 7.079 em 29 títulos.
```

(`7.0793103448275865` e `29` são também o que o Trino devolve para o Japão:
`SELECT count(*), avg(rating) FROM refined.ml.fct_titles f JOIN
refined.ml.bridge_title_country b ON b.title_key = f.title_key WHERE b.country_key = 'Japan'`.)

O ranking é ordenado no cliente — a ferramenta devolve as linhas; o contrato
governado é medidas × dimensões, filtros e limite. `python mcp/demo.py "por gênero"`
roda a outra pergunta do roteiro.

## Testes

```bash
make mcp-test
```

O Cube entra mockado: `tests/fake_cube.py` serve as respostas gravadas em
`testdata/` (`/meta` e `/load`), e o cliente fala com o servidor pelo protocolo MCP
(stdio). Os testes verificam **equivalência ao resultado do Cube**: o catálogo que o
agente enxerga, a tabela devolvida por `query` e exatamente a chamada que chega ao
Cube — mais os caminhos de erro (membro inventado não vira consulta).

As fixtures foram gravadas do Cube real, com o stack no ar. Para regravar:

```bash
curl -s http://localhost:4000/cubejs-api/v1/meta > mcp/testdata/meta.json

curl -sG http://localhost:4000/cubejs-api/v1/load \
  --data-urlencode 'query={"measures":["titles_overview.count_titles","titles_overview.avg_rating"],"dimensions":["titles_overview.country"],"limit":5}' \
  > mcp/testdata/load_country.json

curl -sG http://localhost:4000/cubejs-api/v1/load \
  --data-urlencode 'query={"measures":["titles_overview.count_titles","titles_overview.avg_rating"],"dimensions":["titles_overview.country"],"filters":[{"member":"titles_overview.count_titles","operator":"gte","values":["20"]}],"limit":5}' \
  > mcp/testdata/load_country_min20.json
```

## Detalhes que a aula costuma perguntar

- **Dev mode**: a REST API não exige token (`CUBEJS_DEV_MODE=true` em `cube/.env`,
  ambiente didático); a SQL API, que o Superset usa, tem credenciais explícitas.
- **Prefixo real da REST**: a spec chama de `/v1/*`; o Cube serve em
  `/cubejs-api/v1/*` — é o que o cliente deste servidor usa.
- **País tem um balde NULL**: a ponte é inner join no dbt, mas o Cube faz LEFT JOIN
  ao fatiar por dimensão de ponte, então títulos sem país aparecem numa linha
  `country = null` (36 dos 1813). Quem pergunta por país filtra
  `{"member": "titles_overview.country", "operator": "set"}` — o que o demo faz
  (por isso 15 países, não 16). Ver `cube/README.md`.
