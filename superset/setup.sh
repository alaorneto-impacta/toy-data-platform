#!/usr/bin/env bash
# Inicialização do Superset: metadata DB, admin e assets padrão.
# Roda a cada `docker compose up`, então precisa ser idempotente.
set -e

# Sai com erro se o admin já existe (segundo boot em diante) — não é falha.
superset fab create-admin \
  --username admin \
  --firstname Superset \
  --lastname Admin \
  --email admin@localhost \
  --password secret \
  || echo "aviso: usuário admin já existe; seguindo"

superset db upgrade
superset init

exec /usr/bin/run-server.sh
