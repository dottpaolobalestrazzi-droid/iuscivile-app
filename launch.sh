#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
set -a; source .env; set +a
mkdir -p data
echo "Backend pronto su http://127.0.0.1:8000"
uvicorn server:app --host 0.0.0.0 --port 8000
