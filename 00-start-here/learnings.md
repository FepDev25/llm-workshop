# Learning hello-agent

Aquí creé un agente simple usando la librería nativa de Ollama. Este agente es capaz de responder preguntas generales y realizar cálculos usando la herramienta calculator. Es un buen punto de partida para entender cómo funcionan los agentes con Ollama y cómo se pueden integrar herramientas para mejorar sus capacidades.

## Tool calling

El agente utiliza el formato de tool calling nativo de Ollama, donde el modelo indica explícitamente cuándo quiere usar una herramienta y qué input le da.

## Decisión de tool o respuesta directa

El agente decide si necesita usar la herramienta calculator o si puede responder directamente. Esto se hace analizando la respuesta del modelo para ver si contiene una indicación de usar la herramienta.

## Memoria

El agente mantiene un historial completo de la conversación, incluyendo las preguntas del usuario, las respuestas del modelo, las llamadas a herramientas y los resultados de esas herramientas. Esto permite que el agente tenga contexto completo en cada paso de la interacción.

## Resumen

- Agente simple con Ollama usando tool calling nativo
- Decisión entre respuesta directa o uso de herramienta
- Memoria completa de la conversación para contexto
