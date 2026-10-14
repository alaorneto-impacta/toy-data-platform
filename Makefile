DBT_IMAGE = movies_transform
DBT_TARGET ?= dev
NETWORK = platform-net
DLT_IMAGE = my-dlt-pipeline
DLT_TABLE ?= imdb_top_1000

build: 
	docker build -t $(DBT_IMAGE) dbt/

# --- dlt ingestion (official path: run inside the Compose network) ---

dlt-build:
	docker build -t $(DLT_IMAGE) dlt/

# Requires the stack to be up (`docker compose up -d`).
# Pick the CSV to ingest with DLT_TABLE, e.g. `make dlt-run DLT_TABLE=netflix_titles`.
dlt-run: dlt-build
	docker run --rm \
	    --env-file $(PWD)/dlt/.env.docker \
	    --network $(NETWORK) \
	    $(DLT_IMAGE) \
	    python filesystem_pipeline.py -t $(DLT_TABLE)

dbt-shell:
	docker run --rm -v $(PWD)/dbt/$(DBT_IMAGE):/usr/app/$(DBT_IMAGE) \
	    -e DBT_TARGET=$(DBT_TARGET) \
	    -e DBT_TARGET_PATH=target/$(DBT_TARGET) \
	    -p 8082:8082 \
	    --env-file $(PWD)/dbt/.env \
		--network $(NETWORK) \
		-w /usr/app/$(DBT_IMAGE) -it $(DBT_IMAGE) \
		bash

docs-generate:
	docker run --rm \
	  -v $(PWD)/dbt/$(DBT_IMAGE):/usr/app/$(DBT_IMAGE) \
	  --env-file $(PWD)/dbt/.env \
	  -e DBT_TARGET=$(DBT_TARGET) \
	  --network $(NETWORK) \
	  -w /usr/app/$(DBT_IMAGE) \
	  $(DBT_IMAGE) \
	  dbt docs generate

docs: docs-generate
	docker run --rm \
	  -v $(PWD)/dbt/$(DBT_IMAGE):/usr/app/$(DBT_IMAGE) \
	  --env-file $(PWD)/dbt/.env \
	  -e DBT_TARGET=$(DBT_TARGET) \
	  -p 8082:8082 \
	  --network $(NETWORK) \
	  -w /usr/app/$(DBT_IMAGE)/target \
	  -it $(DBT_IMAGE) \
	  python3 -m http.server 8082

# --- agente MCP (roda no host, fala com o Cube publicado em localhost:4000) ---

mcp-install:
	python3 -m venv mcp/.venv && mcp/.venv/bin/pip install -r mcp/requirements.txt

mcp-test:
	mcp/.venv/bin/python -m unittest discover -s mcp/tests -v

mcp-demo:
	mcp/.venv/bin/python mcp/demo.py