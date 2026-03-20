#!/usr/bin/env python3
# Hello Agent: Primer agente con Ollama
# Este agente usa tool calling simple y directo con la librería ollama nativa.

import ollama

# evalua expresiones matematicas de forma segura
def calculator(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Error: Caracteres no permitidos"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

# agente simple con tool calling nativo
class SimpleAgent:
    def __init__(self, model="llama3.1"):
        self.model = model
        self.client = ollama.Client()
        self.history = [] # historial de conversacion para contexto

    def get_system_prompt(self):
        return """Eres un asistente útil. Puedes usar la herramienta 'calculator' para matemáticas.

Para usar la calculadora, responde EXACTAMENTE así:
TOOL: calculator
INPUT: <expresión matemática>

Ejemplo:
TOOL: calculator
INPUT: 34 * 21

Cuando recibas [TOOL_RESULT], usa ese valor para responder directamente al usuario."""

    # extrae llamada a herramienta del texto
    def parse_tool(self, text):
        lines = text.strip().split("\n")
        tool_name = None
        tool_input = None

        for _, line in enumerate(lines):
            if line.startswith("TOOL:"):
                tool_name = line.replace("TOOL:", "").strip()
            elif line.startswith("INPUT:"):
                tool_input = line.replace("INPUT:", "").strip()

        return tool_name, tool_input

    # procesa input del usuario
    def chat(self, user_input):

        # agregar mensaje del usuario al historial
        self.history.append({"role": "user", "content": user_input})

        # preparar el contexto, system prompt + historial de conversación
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + self.history

        print("Pensando...")
        # primer llamada al modelo, puede: responder o pedir usar herramienta
        response = self.client.chat(model=self.model, messages=messages)
        assistant_msg = response["message"]["content"] # se obtiene el texto de la respuesta del modelo

        # verificar si se debe usar tool
        tool_name, tool_input = self.parse_tool(assistant_msg)

        if tool_name == "calculator" and tool_input:
            print(f"Calculando: {tool_input}")
            result = calculator(tool_input)
            print(f"Resultado: {result}")

            # agrega la interacción al historial
            self.history.append({"role": "assistant", "content": assistant_msg})
            self.history.append(
                # marcar que es resultado de herramienta para que el modelo lo entienda claramente
                {"role": "user", "content": f"[TOOL_RESULT] {tool_name}: {result}"}
            )

            # pedir respuesta final
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ] + self.history

            # segunda llamada al modelo, se espera respuesta final usando herramienta
            final = self.client.chat(model=self.model, messages=messages)
            final_msg = final["message"]["content"]
            self.history.append({"role": "assistant", "content": final_msg})

            return final_msg
        else:
            # respuesta directa
            self.history.append({"role": "assistant", "content": assistant_msg})
            return assistant_msg


def main():
    print("\n" + "*" * 60)
    print("HELLO AGENT - Primer agente con Ollama")
    print("*" * 60)
    print("\nModelo: llama3.1 (local)")
    print("Tool: calculator")
    print("\nComandos: 'salir' | 'limpiar'")
    print("Ejemplos: \n'Cuánto es 34 * 21?'")
    print("'Dime los paises de América del Sur'\n")
    print("*" * 60 + "\n")

    agent = SimpleAgent()
    print("Agente listo\n")

    while True:
        try:
            user_input = input("Tú: ").strip()

            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\nAdios...")
                break

            if user_input == "limpiar":
                agent.history = []
                print("Conversación reiniciada")
                continue

            if not user_input:
                continue

            response = agent.chat(user_input)
            print(f"\nAgente: {response}\n")

        except KeyboardInterrupt:
            print("\n\nAdios...")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
