# Document loader - Carga y validacion de archivos de texto.
from pathlib import Path
from typing import List

# Carga documento de texto desde archivos .txt o .md, con manejo de encoding.
class DocumentLoader:
    SUPPORTED_EXTENSIONS = (".txt", ".md")

    # Carga un archivo, recibe la ruta del archivo, devuelve el contenido como string
    # excepciones: FileNotFoundError, UnicodeDecodeError
    def load_file(self, filepath: Path) -> str:
        # Intentar UTF-8 primero
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback a latin-1
            with open(filepath, "r", encoding="latin-1") as f:
                return f.read()

    # carga todos los documentos en un directorio, devuelve lista de string con contenido de cada documento
    def load_directory(self, directory: str) -> List[str]:
        docs_path = Path(directory)

        if not docs_path.exists():
            print(f"Directorio no encontrado: {directory}")
            return []

        documents = []

        for filepath in docs_path.iterdir():
            if (filepath.is_file() and filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS):
                try:
                    # llama a load_file para cada archivo, agrega el contenido a la lista de documentos
                    content = self.load_file(filepath)
                    documents.append(content)
                    print(f"  Cargado: {filepath.name}")
                except Exception as e:
                    print(f"Error cargando {filepath.name}: {e}")

        return documents
