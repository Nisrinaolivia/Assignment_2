"""
Retrieval-augmented generation (RAG) over Part 4 of the OAIC guide
'Data breach preparation and response' (knowledge/oaic_guide.json).

How it works:
1. The guide was split into ~100 passages, each tagged with its page and section.
2. Each step of the assessment searches only the sections relevant to it
   (e.g. the serious-harm step only searches the serious-harm guidance and examples).
3. Within those sections, passages are ranked by semantic similarity using OpenAI
   embeddings. If embeddings are unavailable, a keyword-overlap ranking is used instead.
4. The top passages are given to the AI with a citation label (e.g. [OAIC p 35]),
   and the AI is asked to cite the passages it relies on.
"""

import json
import math
import re
from pathlib import Path

import streamlit as st

GUIDE_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "oaic_guide.json"
EMBEDDING_MODEL = "text-embedding-3-small"

# Which sections of the guide each step is allowed to search.
STEP_SECTIONS = {
    "entity": ["Entities covered by the NDB scheme", "Data breaches involving more than one entity"],
    "element_1": ["Identifying eligible data breaches"],
    "element_2": ["Identifying eligible data breaches"],
    "remedial": ["Identifying eligible data breaches"],
    "statement": [
        "What to include in an eligible data breach statement",
        "Notifying individuals about an eligible data breach",
    ],
}

# Sub-sections to prefer for each step (passages here get a small ranking boost).
STEP_PREFERRED = {
    "element_1": ["What is a ‘data breach’?", "Eligible data breach"],
    "element_2": [
        "Is serious harm likely?",
        "The type or types of personal information",
        "Circumstances of the data breach",
        "The nature of the harm",
        "Example",
    ],
    "remedial": ["Preventing serious harm with remedial action", "Example"],
}


@st.cache_data
def load_guide():
    data = json.loads(GUIDE_PATH.read_text(encoding="utf-8"))
    return data["chunks"], data["source"]


@st.cache_resource(show_spinner="Indexing the OAIC guide (first run only)...")
def _guide_embeddings(_client):
    """Embeds every passage once per server session. `_client` is not hashed."""
    chunks, _ = load_guide()
    texts = [f"{c['section']} — {c['subsection']}: {c['text']}" for c in chunks]
    resp = _client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _tokens(text):
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def retrieve(client, step, query, k=4):
    """Returns the k most relevant passages for a step, plus the method used."""
    chunks, _ = load_guide()
    allowed = STEP_SECTIONS.get(step)
    preferred = STEP_PREFERRED.get(step, [])
    idx = [i for i, c in enumerate(chunks) if not allowed or c["section"] in allowed]

    method = "semantic (embeddings)"
    try:
        doc_vecs = _guide_embeddings(client)
        q_vec = client.embeddings.create(model=EMBEDDING_MODEL, input=[query]).data[0].embedding
        scores = {i: _cosine(q_vec, doc_vecs[i]) for i in idx}
    except Exception:
        method = "keyword overlap (embeddings unavailable)"
        q = _tokens(query)
        scores = {i: len(q & _tokens(chunks[i]["text"])) / (len(q) or 1) for i in idx}

    for i in idx:
        if any(chunks[i]["subsection"].startswith(p) for p in preferred):
            scores[i] += 0.03

    top = sorted(idx, key=lambda i: scores[i], reverse=True)[:k]
    passages = [dict(chunks[i], score=round(scores[i], 3)) for i in top]
    return passages, method


def cite(passage):
    return f"[OAIC p {passage['page']}]"


def format_context(passages):
    """Formats passages for the prompt, each with its citation label."""
    blocks = []
    for p in passages:
        heading = p["section"] + (f" — {p['subsection']}" if p["subsection"] else "")
        blocks.append(f"{cite(p)} {heading}\n{p['text']}")
    return "\n\n".join(blocks)
