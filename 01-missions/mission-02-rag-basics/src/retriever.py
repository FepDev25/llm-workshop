# retriever: busqueda y recuperacion de contexto

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.vector_store import VectorStore
    from src.embedder import Embedder

# recupera contexto relevante para queries, coordinando embedding de queries y busqueda en vector store
class Retriever:

    # inicia el retriver, recibe vector store, embedder y numero de documentos a recuperar
    def __init__(self, vector_store: "VectorStore", embedder: "Embedder", top_k: int = 3):

        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = top_k

    # recupera contexto relevante para una query, recibe query y retorna contexto concatenado de documentos relevantes
    def retrieve(self, query: str) -> str:

        # Generar embedding de la query
        query_embedding = self.embedder.embed_query(query)

        # Buscar documentos similares
        results = self.vector_store.search(query_embedding, top_k=self.top_k)

        # Extraer documentos
        documents = results.get("documents", [[]])[0]

        if not documents:
            return ""

        # Concatenar contexto
        context = "\n\n---\n\n".join(documents)

        return context
