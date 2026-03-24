import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

load_dotenv()

# Configuration
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 64

# Connexion Qdrant
client = qdrant_client.QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

# Chargement des documents
print("Chargement des documents...")
documents = SimpleDirectoryReader("docs", recursive=True).load_data()
print(f"{len(documents)} chunks chargés")

# Création de l'index vectoriel
vector_store = QdrantVectorStore(client=client, collection_name="acenos_kb")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

print("Indexation en cours... (30-60 secondes)")
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
print("Indexation terminée !")