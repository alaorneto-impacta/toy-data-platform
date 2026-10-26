FROM apache/superset:6.1.0

USER root

# Driver do Postgres: serve o metadata DB do Superset e também a conexão com o
# Cube, cuja SQL API fala protocolo Postgres. A imagem 6.x não traz driver de
# banco nenhum (nem para o próprio metadata DB), então isto é obrigatório.
# Mesma versão declarada no extra `postgres` do apache-superset 6.1.0.
RUN uv pip install --python /app/.venv/bin/python \
    "psycopg2-binary==2.9.9" \
    "trino[sqlalchemy]"

COPY --chmod=777 superset_config.py bootstrap_semantic_layer.py /app/
ENV SUPERSET_CONFIG_PATH /app/superset_config.py

USER superset
ENTRYPOINT [ "/usr/bin/run-server.sh" ]
