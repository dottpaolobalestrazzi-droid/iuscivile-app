from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import os, json, numpy as np, faiss, httpx
from openai import OpenAI

app = FastAPI(title="IusCivile RAG + Web + Quiz", version="1.2.0")

DATA_DIR = os.environ.get("IUS_DATA", "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
META_PATH = os.path.join(DATA_DIR, "meta.json")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CX = os.environ.get("GOOGLE_CX", "")
MODEL_EMB = os.environ.get("IUS_EMB_MODEL", "text-embedding-3-large")
MODEL_CHAT = os.environ.get("IUS_CHAT_MODEL", "gpt-4.1-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

ALLOWLIST = [
    "cortedicassazione.it",
    "italgiure.giustizia.it",
    "giustizia-amministrativa.it",
    "cortecostituzionale.it",
    "normattiva.it",
    "gazzettaufficiale.it",
    "eur-lex.europa.eu",
    "curia.europa.eu",
    "hudoc.echr.coe.int",
]

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]]
    profile: str = "praticanteAvvocato"
    show_links: bool = True
    force_web_for_cases: bool = True
    top_k: int = 8

class ChatResponse(BaseModel):
    answer: str
    citations: List[str]

class QuizRequest(BaseModel):
    topic: str
    difficulty: str = "medio"  # facile/medio/difficile
    num: int = 5

class QuizItem(BaseModel):
    question: str
    options: List[str]
    correct_index: int
    explanation: str | None = None
    references: List[str] | None = None

class QuizResponse(BaseModel):
    items: List[QuizItem]

def _load_index():
    if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
        return None, []
    index = faiss.read_index(INDEX_PATH)
    meta = json.load(open(META_PATH, "r", encoding="utf-8"))
    return index, meta

def _embed_texts(texts: List[str]) -> np.ndarray:
    if client is None:
        rng = np.random.default_rng(0)
        return rng.normal(size=(len(texts), 1536)).astype("float32")
    res = client.embeddings.create(model=MODEL_EMB, input=texts)
    import numpy as _np
    vecs = [_np.array(d.embedding, dtype="float32") for d in res.data]
    return _np.stack(vecs, axis=0)

def _search_local(query: str, top_k: int = 8):
    index, meta = _load_index()
    if index is None: return []
    qv = _embed_texts([query])
    D, I = index.search(qv, top_k)
    hits = []
    for dist, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(meta): continue
        hits.append((float(dist), meta[idx]))
    return hits

def _looks_like_case_query(q: str) -> bool:
    keys = ["sentenza", "cass", "giurisprudenza", "sezioni unite", "corte cost", "cgUe", "cedu"]
    return any(k in q.lower() for k in keys)

async def google_search(query: str, allowlist=ALLOWLIST, num=10) -> List[Dict[str, Any]]:
    if not GOOGLE_API_KEY or not GOOGLE_CX: return []
    q = query + " " + " OR ".join([f"site:{d}" for d in allowlist])
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": q, "num": num}
    async with httpx.AsyncClient(timeout=20) as s:
        r = await s.get(url, params=params)
        if r.status_code != 200: return []
        data = r.json()
        items = data.get("items", [])
        return [{"title": it.get("title",""), "link": it.get("link",""), "snippet": it.get("snippet","")} for it in items]

def normalize_citation(title: str, snippet: str) -> str:
    t = (title or "") + " " + (snippet or "")
    return t.strip()[:160]

def build_prompt(profile: str, query: str, contexts: List[str], web_refs: List[str], show_links: bool) -> List[Dict[str, str]]:
    system = "Sei un assistente giuridico (diritto civile IT). Cita SOLO norme e giurisprudenza; niente dottrina protetta. Se i dati sono incerti, indicalo."
    if profile == "praticanteAvvocato":
        system += " Taglio forense operativo: onere della prova, termini, rimedi; checklist finale. Struttura: Quesito -> Norme -> Giurisprudenza -> Applicazione -> Conclusioni."
    elif profile == "avvocato":
        system += " Taglio professionale: strategia processuale, rischi, orientamenti consolidati, spese e rito; richiami a SU ove rilevanti."
    elif profile == "praticanteNotaio":
        system += " Taglio notarile: qualificazione, causa, forma, clausole, rischi, adempimenti post stipula; massime notarili verificate."
    elif profile == "notaio":
        system += " Approfondimento notarile: varianti e red flags; massime CN Milano ove rilevanti."
    else:
        system += " Taglio didattico con definizioni chiare e schemi."
    user = "Quesito: " + query + "\n\nContesto recuperato (usa solo ciò che è pertinente):\n" + "\n---\n".join(contexts[:8])
    if web_refs:
        user += "\n\nRiferimenti web (usa solo per giurisprudenza effettiva):\n" + "\n".join(web_refs[:8])
    return [{"role":"system","content":system},{"role":"user","content":user}]

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    hits = _search_local(req.query, top_k=req.top_k)
    contexts = [h[1].get("chunk","") for h in hits]
    web_items = []
    if req.force_web_for_cases or _looks_like_case_query(req.query):
        web_items = await google_search(req.query)
    web_citations = []
    for it in web_items:
        c = normalize_citation(it.get("title",""), it.get("snippet",""))
        if req.show_links and it.get("link"): c = f"{c} — {it['link']}"
        web_citations.append(c)
    if client is None:
        demo = "Modalità sviluppo: indice locale attivo, ma nessun LLM.\nContesto:\n- " + "\n- ".join(contexts[:3])
        if web_citations: demo += "\n\nRiferimenti web:\n- " + "\n- ".join(web_citations[:3])
        return ChatResponse(answer=demo, citations=web_citations[:8])
    messages = build_prompt(req.profile, req.query, contexts, web_citations if req.show_links else [], req.show_links)
    resp = client.chat.completions.create(model=MODEL_CHAT, messages=messages, temperature=0.2)
    text = resp.choices[0].message.content
    return ChatResponse(answer=text, citations=web_citations[:8])

# QUIZ endpoint
@app.post("/quiz", response_model=QuizResponse)
async def quiz(req: QuizRequest):
    prompt = f"""Genera {req.num} domande a risposta multipla (4 opzioni) sulla teoria di diritto civile italiano.
Argomento: {req.topic}
Difficoltà: {req.difficulty}
Formato JSON con chiavi: question, options (array di 4), correct_index (0-3), explanation (breve), references (norme/giurisprudenza essenziali).
Rispetta rigorosamente il JSON, senza testo extra.
"""
    if client is None:
        # demo stub
        items = [{
            "question":"Che cos'è l'obbligazione?",
            "options":["Un dovere morale","Un vincolo giuridico a una prestazione","Un diritto reale","Una sanzione"],
            "correct_index":1,
            "explanation":"L'obbligazione è un vincolo giuridico a una prestazione (art. 1173 ss. c.c.).",
            "references":["art. 1173 c.c.", "art. 1174 c.c."]
        }]
        return QuizResponse(items=[QuizItem(**it) for it in items])
    # Real generation
    msg = [{"role":"system","content":"Sei un generatore di quiz per diritto civile italiano. Produci solo JSON valido."},
           {"role":"user","content": prompt}]
    r = client.chat.completions.create(model=MODEL_CHAT, messages=msg, temperature=0.2)
    raw = r.choices[0].message.content or "[]"
    try:
        data = json.loads(raw)
        items = [QuizItem(**it) for it in data]
    except Exception:
        # fallback: single item
        items = [QuizItem(question="Parsing fallito, riprova", options=["OK","NO","BOH","RIPROVA"], correct_index=0, explanation=None, references=None)]
    return QuizResponse(items=items)
