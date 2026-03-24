import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings, PromptTemplate
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.postprocessor.cohere_rerank import CohereRerank
import qdrant_client

load_dotenv()

# Configuration LLM + embeddings
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = Anthropic(model="claude-sonnet-4-5", api_key=os.getenv("ANTHROPIC_API_KEY"))

# Connexion Qdrant
client = qdrant_client.QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)
vector_store = QdrantVectorStore(client=client, collection_name="acenos_kb")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

# Re-ranker Cohere (améliore la pertinence des résultats)
reranker = CohereRerank(api_key=os.getenv("COHERE_API_KEY"), top_n=5)

# Prompt système ACENOS
SYSTEM_PROMPT = """Tu es l'agent de connaissances ACENOS, assistant expert pour les consultants 
du cabinet de conseil en transformation digitale pour les directions financières bancaires.
Tu réponds exclusivement à partir de la base de connaissances ACENOS.
Tu cites toujours tes sources (nom du document).
Tu réponds en français, avec un ton professionnel et synthétique.
Si l'information n'est pas dans la base, dis-le clairement plutôt que d'inventer."""

def get_query_engine():
    return index.as_query_engine(
        similarity_top_k=10,           # Récupère 10 chunks
        node_postprocessors=[reranker], # Re-rank pour garder les 5 meilleurs
        system_prompt=SYSTEM_PROMPT,
    )