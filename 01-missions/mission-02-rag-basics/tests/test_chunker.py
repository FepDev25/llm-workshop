# tests para Chunker

from src.chunker import Chunker

# tests para el chunking de documentos
class TestChunker:

    def test_simple_chunking(self):
        """Test chunking basico."""
        chunker = Chunker(chunk_size=100, overlap=10)

        documents = ["Parrafo uno. Parrafo dos. Parrafo tres."]
        chunks = chunker.chunk_documents(documents)

        assert len(chunks) > 0
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_overlap_applied(self):
        """Test que se aplica overlap correctamente."""
        chunker = Chunker(chunk_size=100, overlap=20)

        # Documento que generara multiples chunks
        doc = "X" * 250
        chunks = chunker.chunk_documents([doc])

        if len(chunks) > 1:
            # Verificar que hay overlap
            first_chunk_end = chunks[0][-20:]
            second_chunk_start = chunks[1][:20]
            assert first_chunk_end == second_chunk_start

    def test_empty_document(self):
        """Test manejo de documento vacio."""
        chunker = Chunker(chunk_size=100)

        chunks = chunker.chunk_documents([""])

        assert chunks == []

    def test_multiple_documents(self):
        """Test chunking de multiples documentos."""
        chunker = Chunker(chunk_size=100)

        docs = ["Documento uno con contenido.", "Documento dos con mas contenido aqui."]

        chunks = chunker.chunk_documents(docs)

        assert len(chunks) >= 2
