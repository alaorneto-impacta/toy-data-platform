# dlt — ingestão de CSV para o catálogo Iceberg

Os CSVs em `data/` são ingeridos como tabelas Iceberg no catálogo (Lakekeeper),
gravando os arquivos no MinIO. Depois da ingestão a tabela aparece no Trino.

## Caminho oficial (container, na rede do Compose)

O dlt roda **dentro da rede Docker**, onde os nomes de serviço (`minio`,
`lakekeeper`) resolvem. Este é o único caminho que funciona sem configuração de
sistema na máquina do aluno.

```bash
docker compose up -d      # sobe o stack (MinIO, Lakekeeper, Trino, ...)
make dlt-run              # ingere data/imdb_top_1000.csv
```

Para escolher a tabela (aula dirigida), informe o nome do CSV sem a extensão:

```bash
make dlt-run DLT_TABLE=netflix_titles
make dlt-run DLT_TABLE=meta_critic
```

Reexecutar o comando substitui os dados da tabela (`write_disposition="replace"`),
sem linhas duplicadas. A configuração usada é `dlt/.env.docker` (nomes de
serviço).

Para conferir no Trino:

```sql
SELECT count(*) FROM raw.raw_movies.imdb_top_1000;
```

## Caminho opcional (host / venv)

Rodar o dlt direto no host é possível, mas **é o caminho secundário**: ele não
esconde o Docker e depende de um pré-requisito.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

set -a; source .env.host; set +a
python filesystem_pipeline.py -t imdb_top_1000
```

### Por que o pré-requisito existe

Com um **catálogo REST**, o cliente (pyiceberg) descobre o *endpoint de storage*
a partir da resposta do catálogo — ele **não** pode ser sobrescrito pelo destino
`filesystem` do dlt. O warehouse `raw` aponta para o endereço interno do MinIO
(`http://minio:9000`), então o host precisa resolver esse nome:

```bash
# /etc/hosts
127.0.0.1 minio
```

Sem essa linha a gravação falha por resolução de nome/conexão — não é bug do
código, é consequência de a arquitetura de catálogo definir como os clientes
falam com o storage. Por isso o caminho oficial é o container, que já está na
rede onde `minio` resolve.

## Configuração

Duas configurações por contexto:

| Arquivo | Contexto | Endereços |
| --- | --- | --- |
| `dlt/.env.docker` | container na rede do Compose | nomes de serviço (`minio`, `lakekeeper`) |
| `dlt/.env.host` | host / venv (opcional) | `localhost` |

Chaves relevantes:

- `PYICEBERG_CATALOG__RAW__URI` / `..._WAREHOUSE` — definem o catálogo `raw` para
  o pyiceberg (`uri`, `warehouse`).
- `ICEBERG_CATALOG__ICEBERG_CATALOG_NAME` / `..._TYPE` — selecionam o catálogo
  que o dlt carrega (`raw`, `rest`).

> A variável `ICEBERG_CATALOG__ICEBERG_CATALOG_CONFIG__URI` foi removida: o dlt
> **ignora** sub-chaves de um campo de dicionário passadas por variável de
> ambiente, ou seja, era configuração morta. Quem define `uri`/`warehouse` são as
> variáveis `PYICEBERG_CATALOG__RAW__*`.

## Build da imagem

```bash
make dlt-build      # docker build -t my-dlt-pipeline dlt/
```

A mesma imagem é usada pelo DAG do Airflow (`airflow/dags/extract_movies.py`).
