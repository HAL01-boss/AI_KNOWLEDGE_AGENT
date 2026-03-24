import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

load_dotenv()

# --- Configuration ---
DOSSIER_ACENOS = r"C:\Users\HoudaALOUANE\ACENOS"  # chemin vers le dossier à ingérer

EXTENSIONS_AUTORISEES = [".pdf", ".docx", ".pptx", ".txt", ".xlsx"]

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 64

# --- Connexion Qdrant ---
client = qdrant_client.QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)
vector_store = QdrantVectorStore(client=client, collection_name="acenos_kb")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# --- Chargement récursif de tous les fichiers ---
print(f" Scan du dossier : {DOSSIER_ACENOS}")
documents = SimpleDirectoryReader(
    input_dir=DOSSIER_ACENOS,
    recursive=True,                        # parcourt tous les sous-dossiers
    required_exts=EXTENSIONS_AUTORISEES,   # filtre les extensions
    filename_as_id=True,                   # évite les doublons si tu re-lances
).load_data()

print(f"{len(documents)} chunks chargés depuis {DOSSIER_ACENOS}")


# --- Indexation ---
print(f"\n Indexation dans Qdrant...")
VectorStoreIndex.from_documents(documents, storage_context=storage_context)
print(" Indexation terminée !")