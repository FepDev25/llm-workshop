# tests para DocumentLoader

import tempfile
from pathlib import Path

from src.document_loader import DocumentLoader

# tests para la carga de documentos
class TestDocumentLoader:

    def test_load_single_file(self):
        """Test carga de archivo unico."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Contenido de prueba")
            temp_path = Path(f.name)

        loader = DocumentLoader()
        content = loader.load_file(temp_path)

        assert content == "Contenido de prueba"

        # Limpieza
        temp_path.unlink()

    def test_load_directory(self):
        """Test carga de directorio completo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear archivos de prueba
            (Path(tmpdir) / "doc1.txt").write_text("Documento 1")
            (Path(tmpdir) / "doc2.txt").write_text("Documento 2")
            (Path(tmpdir) / "ignore.py").write_text("Ignorar")

            loader = DocumentLoader()
            docs = loader.load_directory(tmpdir)

            assert len(docs) == 2
            assert "Documento 1" in docs
            assert "Documento 2" in docs

    def test_load_nonexistent_directory(self):
        """Test manejo de directorio inexistente."""
        loader = DocumentLoader()
        docs = loader.load_directory("/no/existe")

        assert docs == []

    def test_encoding_fallback(self):
        """Test fallback de encoding."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="latin-1"
        ) as f:
            f.write("Texto con caracteres especiales: cañón")
            temp_path = Path(f.name)

        loader = DocumentLoader()
        content = loader.load_file(temp_path)

        assert "cañón" in content

        temp_path.unlink()
