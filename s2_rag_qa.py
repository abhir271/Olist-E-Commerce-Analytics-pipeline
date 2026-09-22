"""
STEP 2: Embeds the 11 business summaries from summaries.json into a
local Chroma vector database, then lets you ask natural-language
questions. Retrieves the most relevant summary/summaries and asks
Claude to answer using only that retrieved context (this is the
actual "RAG" part).

Run:
    python s2_rag_qa.py

Requires ANTHROPIC_API_KEY to already be set as an environment
variable (you did this earlier with setx).
"""

import json
import os
import chromadb
from chromadb.utils import embedding_functions
import anthropic

# ---- Setup ----
client = chromadb.Client()  # in-memory, resets each run (fine for this MVP)

# Free local embedding model — no API key needed for this part
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.create_collection(
    name="olist_business_summaries",
    embedding_function=embedding_fn
)

# Load the summaries we generated in Step 1b
with open("summaries.json", "r", encoding="utf-8") as f:
    summaries = json.load(f)

collection.add(
    documents=summaries,
    ids=[f"summary_{i}" for i in range(len(summaries))]
)

print(f"Embedded {len(summaries)} summaries into Chroma.\n")

# ---- Claude client ----
claude = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment automatically

def answer_question(question, n_results=3):
    # Retrieve most relevant summaries
    results = collection.query(query_texts=[question], n_results=n_results)
    retrieved_chunks = results["documents"][0]

    context = "\n".join(f"- {c}" for c in retrieved_chunks)

    prompt = f"""You are a business analytics assistant. Answer the question
using ONLY the context below. If the context doesn't contain enough
information to answer, say so honestly rather than guessing.

Context:
{context}

Question: {question}

Answer concisely, citing the specific numbers from the context."""

    response = claude.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text, retrieved_chunks

if __name__ == "__main__":
    print("RAG Business Insights Assistant — type a question (or 'quit' to exit)\n")
    while True:
        q = input("Your question: ").strip()
        if q.lower() in ("quit", "exit"):
            break
        answer, retrieved = answer_question(q)
        print(f"\n--- Retrieved context ---")
        for c in retrieved:
            print(f"  • {c}")
        print(f"\n--- Answer ---\n{answer}\n")