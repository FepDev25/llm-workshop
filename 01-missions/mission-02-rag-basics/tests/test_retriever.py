# Tests para Retriever

from unittest.mock import Mock, MagicMock

from src.retriever import Retriever

# Tests para la recuperacion de contexto
class TestRetriever:

    def test_retrieve_success(self):
        """Test recuperacion exitosa."""
        # Mocks
        mock_store = Mock()
        mock_store.search.return_value = {
            "documents": [["Chunk 1", "Chunk 2"]],
            "distances": [[0.1, 0.2]],
        }

        mock_embedder = Mock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        retriever = Retriever(mock_store, mock_embedder, top_k=2)
        context = retriever.retrieve("query de prueba")

        assert "Chunk 1" in context
        assert "Chunk 2" in context
        assert "---" in context  # Separador

    def test_retrieve_empty(self):
        """Test cuando no hay resultados."""
        mock_store = Mock()
        mock_store.search.return_value = {"documents": [[]]}

        mock_embedder = Mock()
        mock_embedder.embed_query.return_value = [0.1, 0.2]

        retriever = Retriever(mock_store, mock_embedder, top_k=3)
        context = retriever.retrieve("query")

        assert context == ""

    def test_embedder_called_with_query(self):
        """Test que se llama al embedder con la query correcta."""
        mock_store = Mock()
        mock_store.search.return_value = {"documents": [["result"]]}

        mock_embedder = Mock()
        mock_embedder.embed_query.return_value = [0.1]

        retriever = Retriever(mock_store, mock_embedder, top_k=1)
        retriever.retrieve("pregunta especifica")

        mock_embedder.embed_query.assert_called_once_with("pregunta especifica")
