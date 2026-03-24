import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.postprocessor.cohere_rerank import CohereRerank
import qdrant_client
import streamlit as st

# --- Chargement des variables d'environnement ---
load_dotenv()  # local (.env)

# Pour Streamlit Cloud, les secrets écrasent les variables d'env
if hasattr(st, "secrets"):
    for key, value in st.secrets.items():
        os.environ[key] = value

# --- Chargement du prompt système depuis prompt.txt ---
prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# --- Configuration LLM + embeddings ---
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = Anthropic(
    model="claude-sonnet-4-5",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# --- Connexion Qdrant ---
client = qdrant_client.QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

vector_store = QdrantVectorStore(client=client, collection_name="acenos_kb")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(
    vector_store,
    storage_context=storage_context
)

# --- Re-ranker Cohere ---
reranker = CohereRerank(
    api_key=os.getenv("COHERE_API_KEY"),
    top_n=5
)


def get_query_engine():
    """Retourne le moteur de requête RAG avec re-ranking."""
    return index.as_query_engine(
        similarity_top_k=10,
        node_postprocessors=[reranker],
        system_prompt=SYSTEM_PROMPT,
        response_mode="compact",
    )


def format_sources(response) -> str:
    """
    Formate les sources avec fichier, page, score de pertinence et extrait.
    Retourne une chaîne Markdown prête à afficher dans Streamlit.
    """
    sources = []
    seen = set()

    for i, node in enumerate(response.source_nodes):
        meta = node.metadata

        # Récupération des métadonnées disponibles
        fichier = meta.get("file_name", meta.get("filename", "Document inconnu"))
        page = meta.get("page_label", meta.get("page_number", None))
        section = meta.get("section", meta.get("header", None))
        score = node.score if node.score is not None else 0.0

        # Extrait du texte (200 premiers caractères, nettoyé)
        extrait = node.text[:250].replace("\n", " ").strip()
        if len(node.text) > 250:
            extrait += "..."

        # Dédoublonnage par fichier + page
        cle = f"{fichier}-{page}"
        if cle in seen:
            continue
        seen.add(cle)

        # Construction de la ligne source
        ligne = f"**[{i+1}] {fichier}**\n"
        if page:
            ligne += f"  • 📄 Page : {page}\n"
        if section:
            ligne += f"  • 📌 Section : {section}\n"
        ligne += f"  • 🎯 Pertinence : {score:.0%}\n"
        ligne += f"  • 💬 Extrait : *\"{extrait}\"*"

        sources.append(ligne)

    if not sources:
        return "⚠️ Aucune source trouvée dans la base de connaissances."

    return "\n\n---\n\n".join(sources)


# --- Test rapide en terminal ---
if __name__ == "__main__":
    engine = get_query_engine()
    question = input("Ta question : ")
    response = engine.query(question)
    print("\n=== RÉPONSE ===\n")
    print(response)
    print("\n=== SOURCES ===\n")
    print(format_sources(response))