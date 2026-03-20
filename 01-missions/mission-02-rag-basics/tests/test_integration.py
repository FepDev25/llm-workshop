# Tests de integracion para el sistema RAG completo

import tempfile
from pathlib import Path
import pytest

from src.rag_system import RAGSystem

# tests de integracion end-to-end
class TestRAGIntegration:

    @pytest.fixture
    def sample_docs_dir(self):
        """Crea directorio temporal con documentos de prueba."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear documento de prueba
            doc_path = Path(tmpdir) / "test.txt"
            doc_path.write_text(
                "Python es un lenguaje de programacion. "
                "Fue creado por Guido van Rossum. "
                "Es muy popular para ciencia de datos.",
                encoding="utf-8",
            )
            yield tmpdir

    def test_full_pipeline(self, sample_docs_dir):
        """Test del pipeline completo."""
        rag = RAGSystem(
            documents_dir=sample_docs_dir,
            collection_name="test_collection",
            persist_dir="./test_chroma_db",
        )

        # Ingestion
        rag.ingest_documents()

        # Verificar que se cargaron documentos
        stats = rag.get_stats()
        assert stats["document_count"] > 0

    def test_query_without_ingestion(self):
        """Test que falla si no se ingestaron documentos."""
        rag = RAGSystem()

        with pytest.raises(RuntimeError) as exc_info:
            rag.query("test")

        assert "ingest_documents" in str(exc_info.value)

    def test_multiple_queries(self, sample_docs_dir):
        """Test multiples consultas sobre los mismos documentos."""
        rag = RAGSystem(
            documents_dir=sample_docs_dir,
            collection_name="test_multi",
            persist_dir="./test_chroma_db_2",
        )

        rag.ingest_documents()

        # Varias queries
        queries = ["Quien creo Python?", "Para que se usa Python?", "Que es Python?"]

        for query in queries:
            response = rag.query(query)
            # Verificar que retorna string
            assert isinstance(response, str)
            assert len(response) > 0
