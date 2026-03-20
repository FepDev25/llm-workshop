# Learning Mission 02: RAG Basics

Aprendí que RAG es una técnica para responder preguntas basadas en documentos, como lo que hace NotebookLM de Google. Para hacer esto, primero dividimos el documento en chunks, luego convertimos esos chunks en embeddings usando un modelo pre-entrenado. Cuando recibimos una pregunta, también la convertimos en un embedding y buscamos los chunks más relevantes usando similitud coseno. Finalmente, pasamos esos chunks relevantes a un modelo generativo para obtener la respuesta.

## Chunks

Dividir el documento en chunks es importante porque los modelos de lenguaje tienen un límite de tokens que pueden procesar. 
Si el documento es demasiado grande, no podremos enviarlo completo al modelo. 
Si los chunks son demasiado pequeños, podríamos perder contexto importante. 
Se usa overlap entre chunks para asegurarnos de que no perdamos información crítica que podría estar en la frontera entre dos chunks. Esto se refiere a que usamos una pequeña parte del texto del chunk anterior en el siguiente chunk para mantener la continuidad.

## Embeddings

Un embedding es una representación numérica de un texto que captura su significado semántico. 
Usamos similitud coseno en lugar de distancia euclidiana porque la similitud coseno mide la orientación de los vectores en el espacio, lo que es más relevante para comparar significados.

## Retrieval

El proceso de retrieval implica buscar los chunks más relevantes para una pregunta dada.
Si el sistema RAG falla, podría ser porque los embeddings no capturan bien el significado del texto, o porque el modelo generativo no está utilizando la información de los chunks de manera efectiva.

## RAG

La ventaja de RAG es que te responde en base a información específica de los documentos, en lugar de solo basarse en su conocimiento pre-entrenado.
El sistema pueda fallar si los chunks no contienen la información relevante, o si el modelo generativo no puede usar esa información correctamente.
Para mejorar la precisión del retrieval, podríamos usar un modelo de embedding más avanzado, o ajustar los parámetros de búsqueda para obtener resultados más relevantes.

## Bases de datos de vectores como ChromaDB

ChromaDB es una base de datos de vectores que nos permite almacenar y buscar embeddings de manera eficiente.
Cuando ejecutamos el sistema RAG completo, el flujo es:
1. Recibimos una pregunta (query).
2. Convertimos la pregunta en un embedding.
3. Usamos ese embedding para buscar los chunks más relevantes en ChromaDB.
4. Pasamos esos chunks relevantes a un modelo generativo para obtener la respuesta.

## Mi resumen

En resumen, RAG es una técnica poderosa para responder preguntas basadas en documentos, pero requiere una buena gestión de chunks, embeddings y retrieval para funcionar correctamente.