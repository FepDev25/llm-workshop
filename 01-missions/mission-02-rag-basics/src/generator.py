# generator: generacion de respuestas con LLM

import os
from typing import Optional
import ollama

# genera respuestas usando Ollama, construye prompts con contexto recuperado y maneja comunicacion con el modelo LLM
class Generator:

    # iniciar el generador, recibe nombre del modelo y url del servidor, se usa Ollama
    def __init__(self, model: Optional[str] = None, host: Optional[str] = None):

        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host=self.host)

    # genera respuesta basada en contexto, recibe query y contex y retorna respuesta generada por el LLM
    def generate(self, query: str, context: str) -> str:

        system_prompt = self._build_system_prompt(context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        try:
            response = self.client.chat(model=self.model, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            return f"Error generando respuesta: {str(e)}"

    # construye el system prompt con contexto, recibe contexto de documentos y retorna system prompt completo
    def _build_system_prompt(self, context: str) -> str:
        return f"""Eres un asistente experto que responde preguntas basandote UNICAMENTE en el contexto proporcionado.

INSTRUCCIONES:
1. Responde usando SOLO la informacion del contexto proporcionado
2. Si la respuesta no esta en el contexto, di claramente: "No encontre informacion sobre eso en los documentos proporcionados."
3. Se conciso pero completo
4. Si hay informacion contradictoria, mencionalo

CONTEXTO:
{context}
"""
