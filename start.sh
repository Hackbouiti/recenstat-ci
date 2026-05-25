#!/bin/bash
set -e

echo "=== RecenStat-CI — Démarrage ==="

echo "→ Migrations de la base de données..."
flask db upgrade

echo "→ Initialisation des données de référence..."
flask seed

echo "→ Lancement du serveur gunicorn..."
exec gunicorn run:app \
  --bind "0.0.0.0:${PORT:-5000}" \
  --workers 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
