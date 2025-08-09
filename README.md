# Backend — IusCivile Pro+ (RAG + Google CSE + Quiz)

## Setup rapido
```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
export GOOGLE_API_KEY=...
export GOOGLE_CX=...
uvicorn server:app --reload
```

## Indicizza i tuoi PDF
```
mkdir -p data
python ingest.py /path/ai/tuoi/file1.pdf ...
```

## Endpoint
- POST `/chat`
- POST `/quiz`  body: `{ "topic":"obbligazioni", "difficulty":"medio", "num":5 }`
