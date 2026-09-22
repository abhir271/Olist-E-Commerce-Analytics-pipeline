"""
Combined web app: Tableau dashboard (embedded) + RAG chat assistant,
on one page.

Run:
    streamlit run app.py

Requires:
    pip install streamlit chromadb sentence-transformers anthropic

Requires ANTHROPIC_API_KEY set as an environment variable, and
summaries.json (from s1b_generate_summaries.py) in the same folder.
"""

import json
import os
import streamlit as st
import streamlit.components.v1 as components
import chromadb
from chromadb.utils import embedding_functions
import anthropic

st.set_page_config(
    page_title="Olist E-Commerce Analytics + GenAI Insights",
    layout="wide"
)

st.title("Olist E-Commerce Analytics Pipeline")
st.caption("Analytics dashboard + a RAG-powered assistant for natural-language business questions")

# ---------------- Tableau Dashboard Section ----------------
st.header("📊 Dashboard")

TABLEAU_EMBED_CODE = """
<div class='tableauPlaceholder' id='viz1790102233589' style='position: relative'>
<noscript><a href='#'><img alt='Olist E-Commerce Analytics Dashboard ' src='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;Ol&#47;OlistE-CommerceAnalytics_17865833504340&#47;OlistE-CommerceAnalyticsDashboard&#47;1_rss.png' style='border: none' /></a></noscript>
<object class='tableauViz' style='display:none;'>
<param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
<param name='embed_code_version' value='3' />
<param name='site_root' value='' />
<param name='name' value='OlistE-CommerceAnalytics_17865833504340&#47;OlistE-CommerceAnalyticsDashboard' />
<param name='tabs' value='no' />
<param name='toolbar' value='yes' />
<param name='static_image' value='https:&#47;&#47;public.tableau.com&#47;static&#47;images&#47;Ol&#47;OlistE-CommerceAnalytics_17865833504340&#47;OlistE-CommerceAnalyticsDashboard&#47;1.png' />
<param name='animate_transition' value='yes' />
<param name='display_static_image' value='yes' />
<param name='display_spinner' value='yes' />
<param name='display_overlay' value='yes' />
<param name='display_count' value='yes' />
<param name='language' value='en-US' />
</object>
</div>
<script type='text/javascript'>
    var divElement = document.getElementById('viz1790102233589');
    var vizElement = divElement.getElementsByTagName('object')[0];
    vizElement.style.width='100%';
    vizElement.style.height='900px';
    var scriptElement = document.createElement('script');
    scriptElement.src = 'https://public.tableau.com/javascripts/api/viz_v1.js';
    vizElement.parentNode.insertBefore(scriptElement, vizElement);
</script>
"""

components.html(TABLEAU_EMBED_CODE, height=950, scrolling=True)

st.divider()

# ---------------- RAG Chat Section ----------------
st.header("💬 Ask the GenAI Insights Assistant")
st.caption("Ask a natural-language question about the business data — answers are grounded in retrieved data, not guessed.")

@st.cache_resource
def load_rag_system():
    client = chromadb.Client()
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.create_collection(
        name="olist_business_summaries",
        embedding_function=embedding_fn
    )
    with open("summaries.json", "r", encoding="utf-8") as f:
        summaries = json.load(f)
    collection.add(
        documents=summaries,
        ids=[f"summary_{i}" for i in range(len(summaries))]
    )
    api_key = st.secrets.get("ANTHROPIC_API_KEY", None) if hasattr(st, "secrets") else None
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    claude = anthropic.Anthropic(api_key=api_key)
    return collection, claude

collection, claude = load_rag_system()

def answer_question(question, n_results=3):
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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "retrieved" in msg:
            with st.expander("View retrieved context"):
                for chunk in msg["retrieved"]:
                    st.markdown(f"- {chunk.replace('_', chr(92)+'_')}")

user_question = st.chat_input("e.g. Which state has the worst delivery performance?")

if user_question:
    st.session_state.chat_history.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving context and generating answer..."):
            answer, retrieved = answer_question(user_question)
        st.markdown(answer.replace('_', chr(92)+'_'))
        with st.expander("View retrieved context"):
            for chunk in retrieved:
                st.markdown(f"- {chunk.replace('_', chr(92)+'_')}")

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": answer,
        "retrieved": retrieved
    })