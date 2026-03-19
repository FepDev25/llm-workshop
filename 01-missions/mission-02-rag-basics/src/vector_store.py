# vector sotore: interfaz con chromaDb, para almacenar y recuperar documentos usando embeddings
import os
from typing import List, Dict, Any, Optional
import chromadb

# almacena y recupera documentos usando ChromaDB, con persistencia en disco y busqueda por similitud
class VectorStore:

    # inicializa el vector store, con nombre de la coleccion y directorio de persistencia
    def __init__(self, collection_name: str = "documents", persist_dir: str = "./chroma_db"):

        self.collection_name = collection_name
        self.persist_dir = persist_dir

        # Crear cliente con persistencia
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)

        # Obtener o crear coleccion
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    # agregar documentos a la coleccion, recibe lista de textos, embeddings, metadata opcional
    def add_documents(self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None) -> None:

        if not documents:
            return

        # Generar IDs unicos
        start_idx = self.collection.count()
        ids = [f"doc_{start_idx + i}" for i in range(len(documents))]

        # metadata por defecto
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]

        self.collection.add(
            embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids
        )

    # busca documentos similares, recibe embedding de la query, numero de resultados y retorna
    # resultados: documentos, metadatos y scores de similitud
    def search(self, query_embedding: List[float], top_k: int = 3) -> Dict[str, Any]:

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        return results

    # obtiene estadisticas de la coleccion, retorna diccionario con estas
    def get_stats(self) -> Dict[str, Any]:
        return {
            "collection_name": self.collection_name,
            "document_count": self.collection.count(),
            "persist_dir": self.persist_dir,
        }

    # elimina todos los documentos de la coleccion
    def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )
