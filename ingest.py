import os, json
from typing import List, Dict
import numpy as np, faiss
from pypdf import PdfReader
from openai import OpenAI

DATA_DIR = os.environ.get("IUS_DATA", "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
META_PATH = os.path.join(DATA_DIR, "meta.json")
MODEL_EMB = os.environ.get("IUS_EMB_MODEL", "text-embedding-3-large")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

os.makedirs(DATA_DIR, exist_ok=True)

def read_pdf(path: str) -> str:
    r = PdfReader(path); out = []
    for p in r.pages:
        try: t = p.extract_text() or ""
        except Exception: t = ""
        out.append(t)
    return "\n".join(out)

def chunk_text(t: str, size: int = 2400, overlap: int = 300) -> List[str]:
    chunks = []; i = 0
    while i < len(t):
        chunks.append(t[i:i+size])
        i += (size - overlap)
    return chunks

def embed(texts: List[str]) -> np.ndarray:
    if not OPENAI_API_KEY:
        rng = np.random.default_rng(42); return rng.normal(size=(len(texts), 1536)).astype("float32")
    client = OpenAI(api_key=OPENAI_API_KEY)
    res = client.embeddings.create(model=MODEL_EMB, input=texts)
    vecs = [np.array(d.embedding, dtype="float32") for d in res.data]
    return np.stack(vecs, axis=0)

def main(paths: List[str]):
    metas: List[Dict] = []; chunks_all: List[str] = []
    for p in paths:
        base = os.path.basename(p)
        text = read_pdf(p); chunks = chunk_text(text)
        for j, ch in enumerate(chunks):
            metas.append({"source": base, "chunk": ch, "citation": f"{base} — chunk {j+1}"})
            chunks_all.append(ch)
    X = embed(chunks_all); faiss.normalize_L2(X)
    index = faiss.IndexFlatIP(X.shape[1]); index.add(X)
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w", encoding="utf-8") as f: json.dump(metas, f, ensure_ascii=False, indent=2)
    print(f"Indicizzati {len(chunks_all)} chunk.")
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2: print("Uso: python ingest.py file1.pdf ..."); raise SystemExit(1)
    main(sys.argv[1:])
