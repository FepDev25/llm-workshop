# Glosario de Conceptos — Generative AI

Definiciones de referencia ordenadas temáticamente.
Los conceptos se agregan progresivamente conforme avanzan las misiones.

---

## 00 — Start Here (Hello Agent)

### LLM (Large Language Model)
Modelo de lenguaje de gran escala entrenado en enormes cantidades de texto. Predice el siguiente token dado un contexto. Ejemplos: llama3.1, Gemini, Claude. En este repo se usan modelos locales vía Ollama.

### Ollama
Herramienta que permite correr LLMs de forma local en tu máquina, sin APIs externas ni internet. Expone una API HTTP en `localhost:11434`. En el código se usa con la librería `ollama` de Python.

### Agente (Agent)
Programa que usa un LLM como "cerebro" para decidir qué hacer ante un input. A diferencia de un chat simple, un agente puede ejecutar acciones (herramientas) y usar el resultado para continuar razonando.

```
Usuario → Agente → LLM → ¿necesito herramienta? → Tool → LLM → Respuesta final
```

### System Prompt
Instrucción inicial que define el comportamiento del LLM durante toda la conversación. Se envía con `role: system`. El modelo no lo "olvida" entre mensajes. Es donde se define el contrato de comportamiento del agente.

### Tool Calling (Llamada a herramientas)
Capacidad del agente para ejecutar funciones externas (calculadora, búsqueda web, base de datos, etc.) cuando el LLM decide que las necesita. El LLM no ejecuta la herramienta — solo indica que quiere usarla. El código del agente la ejecuta y devuelve el resultado.

### Conversation History (Historial de conversación)
Lista de mensajes previos (`role: user/assistant/system`) que se envía al LLM en cada llamada. Permite que el modelo "recuerde" el contexto de la conversación. Sin esto, cada llamada sería independiente y el modelo no recordaría nada.

```python
history = [
    {"role": "user",      "content": "Cuánto es 3 * 4?"},
    {"role": "assistant", "content": "TOOL: calculator\nINPUT: 3 * 4"},
    {"role": "user",      "content": "[TOOL_RESULT] calculator: 12"},
]
```

### Parse / Parsing
Proceso de extraer información estructurada de texto libre. En el hello-agent, `parse_tool()` lee la respuesta del LLM y extrae el nombre de la herramienta y su input buscando patrones como `TOOL:` e `INPUT:`.

### Token
Unidad mínima de texto que procesa un LLM. Puede ser una palabra completa, parte de una palabra, o un símbolo. Aproximadamente 1 token ≈ 4 caracteres en inglés, ≈ 3-4 caracteres en español. Los modelos tienen un límite máximo de tokens por llamada (context window).

---

## Mission 02 — RAG Basics

### RAG (Retrieval-Augmented Generation)
Patrón que combina búsqueda de información con generación de texto. En vez de depender solo del conocimiento "memorizado" del LLM durante su entrenamiento, se le inyecta contexto relevante en el momento de la consulta.

```
Query → Buscar documentos relevantes → Contexto → LLM → Respuesta fundamentada
```

**Sin RAG**: el LLM responde con lo que sabe (puede alucinar o estar desactualizado).
**Con RAG**: el LLM responde basándose en documentos reales que le pasás.

### Pipeline RAG
Secuencia de pasos del sistema completo:

```
Ingesta:  Documento → Chunks → Embeddings → Vector Store
Consulta: Query → Embedding → Búsqueda → Contexto → LLM → Respuesta
```

### Embedding
Representación numérica de un texto en forma de vector (lista de números). Textos con significado similar producen vectores matemáticamente cercanos. En mission 02 se usan vectores de 384 dimensiones.

```
"Python es versátil"   → [0.23, -0.15, 0.89, ..., 0.12]  (384 números)
"Python es un lenguaje"→ [0.21, -0.13, 0.87, ..., 0.11]  (cercano)
"El gato duerme"       → [0.01,  0.95, 0.02, ..., 0.78]  (lejano)
```

### Sentence Transformers
Librería que convierte texto en embeddings usando modelos preentrenados. El modelo usado en mission 02 es `all-MiniLM-L6-v2`: liviano (90MB), rápido, y produce vectores de 384 dimensiones. Corre completamente local.

### Chunking
Estrategia de dividir documentos largos en fragmentos más pequeños ("chunks") antes de generar embeddings. Necesario porque los modelos de embedding tienen límite de tokens y porque chunks más pequeños permiten recuperar información más precisa.

### Chunk Size
Tamaño máximo de cada chunk en caracteres. En mission 02: `500 chars ≈ 100 tokens`. Chunks muy grandes pierden precisión en la búsqueda. Chunks muy pequeños pierden contexto.

### Chunk Overlap (Solapamiento)
Cantidad de caracteres del chunk anterior que se repiten al inicio del siguiente. Evita perder contexto en las "costuras" entre chunks. En mission 02: `50 chars (10% del chunk_size)`.

```
Chunk 1: [===================500 chars===================]
Chunk 2:                          [====50====|=====500 chars=====]
                                  ← overlap →
```

### Estrategia de Chunking Jerárquica
Dividir primero por párrafos (`\n\n`) y solo si el párrafo es demasiado largo, dividir por oraciones (`. `). Respeta la estructura semántica del documento en vez de cortar arbitrariamente por caracteres.

### Vector Store
Base de datos especializada en almacenar y buscar vectores de embeddings. Permite encontrar los vectores más similares a una query de forma eficiente. En mission 02 se usa ChromaDB con persistencia en disco.

### ChromaDB
Vector store open source, fácil de usar localmente. Persiste los embeddings en disco (carpeta `chroma_db/`) y permite búsquedas por similitud. No requiere servidor externo.

### Similitud Coseno (Cosine Similarity)
Métrica matemática para medir qué tan parecidos son dos vectores. Mide el ángulo entre ellos (no la distancia). Valor entre -1 y 1, donde 1 = idénticos, 0 = sin relación, -1 = opuestos. Es el estándar para comparar embeddings.

### Top-K
Parámetro que define cuántos chunks similares recuperar por query. En mission 02: `top_k=3` recupera los 3 chunks más relevantes. Más chunks = más contexto pero más ruido y tokens consumidos.

### Retriever
Componente que recibe una query, la convierte a embedding, y busca en el vector store los chunks más similares. Devuelve el contexto concatenado listo para pasarle al LLM.

### Ingesta (Ingest)
Proceso de preparar y cargar documentos en el sistema RAG por primera vez: cargar archivos → chunkear → generar embeddings → guardar en vector store. Se hace una vez (o cuando los documentos cambian).

### Document Loader
Componente que lee archivos del disco (`.txt`, `.md`) y devuelve su contenido como strings. Maneja encoding (UTF-8 con fallback a latin-1) y errores de lectura.

### Context Window
Límite máximo de tokens que un LLM puede procesar en una sola llamada. El contexto RAG (chunks recuperados + pregunta) debe caber dentro de este límite. Con `top_k=3` y `chunk_size=500`, el contexto es ≈1500 chars = ~375 tokens, muy manejable.
