# Embedder: Generacion de embeddings para texto.
# Es convertir texto a números que las máquinas entienden, en esta caso en un vector de dimensiones

from typing import List, Any

# genera embeddings usando sentence-transformers, modelo all-MiniLM-L6-v2 por defecto
class Embedder:

    # inicializa el embedder, carga el modelo de sentence-transformers y obtiene la dimension del embedding
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    # genera embeddings para una lista de chunks, recibe lista de texto y retorna lista de vectores de embedding
    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        if not chunks:
            return []

        embeddings = self.model.encode(chunks, show_progress_bar=True)
        return embeddings.tolist()

    # generar embedding para una query, recibe texto de la pregunta y retorna vector de embedding
    def embed_query(self, query: str) -> List[float]:
        embedding = self.model.encode([query])
        return embedding[0].tolist()
