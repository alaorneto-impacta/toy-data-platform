# Camada semântica — Cube Core

Modelo semântico como código (YAML) sobre o catálogo `refined.ml` no Trino. Declara
**medidas** e **dimensões** governadas e as serve por REST, por SQL API (protocolo
Postgres) e pelo Playground. É a mesma definição que o Superset e o agente MCP consomem.

## Subir

Sobe junto do stack:

```bash
docker compose up -d
```

| Interface | Endereço |
| - | - |
| REST (`/v1/*`) | `http://localhost:4000/cubejs-api/v1` |
| Playground | `http://localhost:4000` |
| SQL API (Postgres) | `localhost:15432` — usuário/senha em `cube/.env` |

A configuração (fonte Trino, credenciais da SQL API) fica em `cube/.env`. A senha do
Trino é intencionalmente vazia: o Trino local não usa TLS e recusa senha em HTTP
(`Password not allowed for insecure authentication`).

## Modelo

`model/cubes/` declara os cubos; `model/views/` a fachada plana que os consumidores usam.

| Cubo | Papel |
| - | - |
| `titles` | Fato no grão de um título. Define as **medidas**. |
| `title_genre` | Ponte título ↔ gênero (dimensão multi-valor). |
| `title_country` | Ponte título ↔ país (dimensão multi-valor). |
| `titles_overview` (view) | Expõe medida + dimensão (`release_year`, `title_type`, `genre`, `country`) num só nome. |

Medidas: `count_titles`, `avg_rating`, `total_votes`. Dimensões: `release_year`,
`title_type`, `genre`, `country`.

Fatiar por uma dimensão multi-valor **não** infla as medidas: o `primary_key:
title_key` no fato faz o Cube deduplicar pelo grão ao atravessar a ponte.

## Consultar

REST:

```bash
curl -sG http://localhost:4000/cubejs-api/v1/load \
  --data-urlencode 'query={
    "measures": ["titles_overview.count_titles", "titles_overview.avg_rating"],
    "dimensions": ["titles_overview.genre"]
  }'
```

SQL API (protocolo Postgres):

```bash
PGPASSWORD=cubecubecube psql -h localhost -p 15432 -U cube -d cube \
  -c "SELECT genre, MEASURE(count_titles), MEASURE(avg_rating)
      FROM titles_overview GROUP BY 1"
```
