
from app.services.llm import generate_response

messages = [
    {
        "role": "user",
        "content": "Explain Python in two simple sentences."
    }
]

try:
    answer = generate_response(messages)

    print("Ollama connection successful!")
    print("\nAI Response:")
    print(answer)

except RuntimeError as error:
    print("Error:", error)
