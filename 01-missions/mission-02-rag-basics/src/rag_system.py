#!/usr/bin/env python3
# implementacion de sistema RAG
# modulo que orquesta todos los componentes del pipeline

import os
import sys
from pathlib import Path
from typing import Optional

from .document_loader import DocumentLoader
from .chunker import Chunker
from .embedder import Embedder
from .vector_store import VectorStore
from .retriever import Retriever
from .generator import Generator

# sistema RAG para consulta de documentos
class RAGSystem:

    """
    inicializa el sistema RAG
        Args:
            documents_dir: Directorio con documentos de entrada
            collection_name: Nombre de la coleccion en ChromaDB
            chunk_size: Tamano maximo de cada chunk en caracteres
            chunk_overlap: Caracteres de superposicion entre chunks
            top_k: Numero de chunks a recuperar por query
            persist_dir: Directorio para persistencia de ChromaDB
        """
    def __init__( self, documents_dir: str = "sample_documents", collection_name: str = "documents", 
        chunk_size: int = 500, chunk_overlap: int = 50, top_k: int = 3, persist_dir: str = "./chroma_db"):
        
        self.documents_dir = documents_dir
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.persist_dir = persist_dir

        # Inicializar componentes
        self.loader = DocumentLoader()
        self.chunker = Chunker(chunk_size=chunk_size, overlap=chunk_overlap)
        self.embedder = Embedder()
        self.vector_store: Optional[VectorStore] = None
        self.retriever: Optional[Retriever] = None
        self.generator = Generator()

    # ejecuta el pipeline completo, carga documentos, divide en chunks, genera embeddings y almacena en vector store
    def ingest_documents(self) -> None:

        print(f"Cargando documentos desde {self.documents_dir}...")
        documents = self.loader.load_directory(self.documents_dir)

        if not documents:
            print("No se encontraron documentos")
            return

        print(f"Cargados {len(documents)} documentos")

        print("Dividiendo en chunks...")
        chunks = self.chunker.chunk_documents(documents)
        print(f"Creados {len(chunks)} chunks")

        print("Generando embeddings...")
        embeddings = self.embedder.embed_chunks(chunks)
        print(f"Generados {len(embeddings)} embeddings")

        print("Almacenando en vector store...")
        self.vector_store = VectorStore(
            collection_name=self.collection_name, persist_dir=self.persist_dir
        )
        self.vector_store.add_documents(chunks, embeddings)
        print("Documentos almacenados correctamente")

        # Inicializar retriever
        self.retriever = Retriever(
            vector_store=self.vector_store, embedder=self.embedder, top_k=self.top_k
        )

    # realiza una consulta al sistema RAG, se pasa le pregunta y retorna la respuesta generada basada en
    #  los documentos, si no se han ingestado documentos lanza un error
    def query(self, question: str) -> str:

        if not self.retriever:
            raise RuntimeError("Se debe ejecutar ingest_documents() antes de consultar")

        print(f"\nProcesando query: {question}")

        # Recuperar contexto relevante
        print("Buscando contexto relevante...")
        context = self.retriever.retrieve(question)

        if not context:
            return "No se encontro informacion relevante para esta pregunta."

        chunks_count = len(context.split("---")) if context else 0
        print(f"Recuperados {chunks_count} chunks")

        # Generar respuesta
        print("Generando respuesta...")
        response = self.generator.generate(question, context)

        return response

    # obtiene estadisticas del sistema
    def get_stats(self) -> dict:
        if not self.vector_store:
            return {"status": "No inicializado"}

        return self.vector_store.get_stats()

# ejecuta el sistema en modo interactivo, se pasa una instancia del sistema RAG iniciada
def interactive_mode(rag: RAGSystem) -> None:

    print("\n" + "*" * 60)
    print("RAG System")
    print("*" * 60)
    print("\nComandos disponibles:")
    print("  query <pregunta>  - Realizar consulta")
    print("  reload            - Recargar documentos")
    print("  stats             - Ver estadisticas")
    print("  exit              - Salir")
    print("*" * 60 + "\n")

    while True:
        try:
            user_input = input("\n>>> ").strip()

            if not user_input:
                continue

            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()

            if command in ["exit", "quit", "salir"]:
                print("Saliendo...")
                break
            elif command == "reload":
                print("\nRecargando documentos...")
                rag.ingest_documents()
                print("Listo\n")
            elif command == "stats":
                stats = rag.get_stats()
                print(f"\nEstadisticas:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            elif command == "query":
                if len(parts) < 2:
                    print("Uso: query <pregunta>")
                    continue
                question = parts[1]
                response = rag.query(question)
                print(f"\nRespuesta:\n{response}\n")
            else:
                # Tratar como query directa
                response = rag.query(user_input)
                print(f"\nRespuesta:\n{response}\n")

        except KeyboardInterrupt:
            print("\n\nSaliendo...")
            break
        except Exception as e:
            print(f"\nError: {e}")

# funcion principal del sistema
def main():

    # Crear documentos de ejemplo si no existen
    create_sample_documents()

    # Inicializar sistema
    rag = RAGSystem()

    # Ingestar documentos
    rag.ingest_documents()

    # Modo interactivo
    interactive_mode(rag)

# Crea documentos de ejemplo si el directorio esta vacio
def create_sample_documents():
    docs_dir = Path("data/sample_docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Verificar si ya hay documentos
    existing = list(docs_dir.glob("*.txt")) + list(docs_dir.glob("*.md"))
    if existing:
        return

    # Crear documento de ejemplo
    content = """# Consejos de Python

Python es un lenguaje de programacion versatil y poderoso.

## List Comprehensions
Las list comprehensions son una forma concisa de crear listas.
En lugar de escribir un bucle for, puedes hacerlo en una linea.
Ejemplo: [x for x in range(10) if x % 2 == 0]

## Manejo de Excepciones
Siempre es buena practica usar try/except para manejar errores.
Especialmente cuando trabajas con archivos o APIs externas.

## Virtual Environments
Usa entornos virtuales para aislar las dependencias de tus proyectos.
UV es una herramienta moderna y rapida para manejar paquetes en Python.

## Type Hints
Anadir anotaciones de tipo hace tu codigo mas legible y mantenible.
Python no las enforcea en runtime, pero herramientas como mypy si.

## Debugging
Usa pdb o breakpoints para depurar codigo complejo.
En Python moderno puedes usar breakpoint() directamente.

## Generadores
Los generadores (yield) son eficientes para manejar grandes volumenes de datos.
No cargan todo en memoria, sino que van produciendo valores uno a uno.

## Decoradores
Los decoradores permiten modificar el comportamiento de funciones.
Son utiles para logging, caching, autenticacion, etc.

## Testing
Escribe tests desde el principio. Usa pytest para testing avanzado.
Los tests te dan confianza para refactorizar codigo.
"""

    file_path = docs_dir / "python_tips.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Creado documento de ejemplo: {file_path}")


if __name__ == "__main__":
    main()
