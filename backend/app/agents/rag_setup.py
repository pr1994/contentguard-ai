import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings
from typing import List

# Suppress the Windows symlink warning to keep console output clean
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Load environment variables
load_dotenv()

class FastEmbedWrapper(Embeddings):
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model_name=model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = list(self.model.embed(texts))
        return [embedding.tolist() for embedding in embeddings]
    
    def embed_query(self, text: str) -> List[float]:
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

# 1. Initialize Qdrant Client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_name = "company_policies"

# 2. Create collection if it doesn't exist
if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

# 3. Mock Company Policies
# Expanded Mock Company Policies
policies = [
    # Legal & Contracts
    "All contracts must have a clear Liability Clause defining financial responsibility.",
    "Contracts must not exceed a duration of 24 months without executive approval.",
    "All vendor agreements must include a Data Privacy and GDPR compliance section.",
    "Risk level must be assessed as Low, Medium, or High based on financial exposure.",
    "Termination clauses must provide at least 30 days notice for both parties.",
    "Intellectual Property (IP) rights must be explicitly assigned to the company upon payment.",
    
    # HR & Employment
    "Employment contracts must include a non-compete clause not exceeding 12 months.",
    "All remote work agreements must specify the approved geographic locations.",
    "Contractor agreements must clearly state they are not eligible for company benefits.",
    
    # Finance & Procurement
    "Any contract exceeding $50,000 requires CFO signature.",
    "Payment terms must be Net-30 or Net-60. Net-90 is strictly prohibited.",
    "Late payment penalties cannot exceed 1.5% per month.",
    
    # IT & Security
    "All software vendor contracts must include an SLA of 99.9% uptime.",
    "Vendors must undergo an annual SOC2 security audit.",
    "Data residency must remain within the country of operation."
]

# 4. Initialize the vector store explicitly (avoids the factory method bug)
embeddings = FastEmbedWrapper()
vector_store = QdrantVectorStore(
    client=client,
    collection_name=collection_name,
    embedding=embeddings
)

# 5. Add texts to the collection
vector_store.add_texts(texts=policies)
print("--- Qdrant Knowledge Base Initialized with Policies ---")