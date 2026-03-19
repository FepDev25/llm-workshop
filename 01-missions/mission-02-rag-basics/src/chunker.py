# Chunker
# Un chunker es una herramienta que divide el texto largo en pedazos manejables para:
# 1. No exceder el tamaño máximo que soporta el embedder                                                                                                                                
# 2. Mantener contexto relevante, o sea no cortar en medio de una idea 

from typing import List

# Divide documentos en chunks semanticos, usa estrategia jerarquica: primero por parrafos, luego por oraciones si es necesario.
class Chunker:

    # inicializa el chunker con tamaño de chunk y overlap
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size # size maximo de cada chunk en caracteres
        self.overlap = overlap # cantidad de caracteres que se superponen entre chunks consecutivos para mantener contexto

    # divide lista de documentos en chunks, recibe la lista y retorna la lista de chunks
    def chunk_documents(self, documents: List[str]) -> List[str]:

        all_chunks = []

        for doc in documents:
            chunks = self._chunk_single_document(doc)
            all_chunks.extend(chunks)

        return all_chunks

    # metodo privado que divide un documento individual, recibe contenido y retorna lista de chunks del documento
    def _chunk_single_document(self, document: str) -> List[str]:

        # Dividir por parrafos primero
        paragraphs = document.split("\n\n")

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip() # eliminar espacios al inicio y final
            if not paragraph:
                continue

            # si el parrafo cabe completo agregarlo
            if len(paragraph) <= self.chunk_size:
                # si el parrafo cabe en el chunk actual, agregarlo con un salto de linea
                if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                    if current_chunk:
                        current_chunk += "\n\n"
                    current_chunk += paragraph
                # si el parrafo no cabe en el chunk actual, agregar el chunk actual a la lista y empezar un nuevo chunk con el parrafo
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = paragraph
            else:
                # Parrafo muy largo, dividir por oraciones
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # Dividir el parrafo en oraciones y agregar cada una como un chunk separado, aplicando overlap si es necesario
                sentence_chunks = self._chunk_by_sentences(paragraph)
                chunks.extend(sentence_chunks)

        # Agregar el ultimo chunk
        if current_chunk:
            chunks.append(current_chunk)

        # Aplicar overlap
        if self.overlap > 0 and len(chunks) > 1:
            chunks = self._apply_overlap(chunks)

        return chunks

    # divide el texto largo por oraciones, recibe texto y retorna lista de chunks de oraciones
    def _chunk_by_sentences(self, text: str) -> List[str]:
        # Separar por punto seguido de espacio
        sentences = text.replace(". ", ".|").split("|")

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += " "
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    # aplica superposicion entre chunks consecutivos, recibe lista de chunks y retorna lista de chunks con overlap aplicado
    def _apply_overlap(self, chunks: List[str]) -> List[str]:

        overlapped = []

        for i, chunk in enumerate(chunks):
            if i > 0:
                # Agregar overlap del chunk anterior
                prev_chunk = chunks[i - 1]
                overlap_text = (
                    prev_chunk[-self.overlap :]
                    if len(prev_chunk) > self.overlap
                    else prev_chunk
                )
                chunk = overlap_text + chunk

            overlapped.append(chunk)

        return overlapped
