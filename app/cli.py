
import requests

API_URL = "http://127.0.0.1:8000/chat/"


def main():
    conversation_id = None

    print("\n=== Chatbot with Persistent Memory ===")
    print("Type 'exit' to quit.\n")

    while True:
        message = input("You: ").strip()

        if message.lower() == "exit":
            print("Goodbye!")
            break

        if not message:
            continue

        try:
            response = requests.post(
                API_URL,
                json={
                    "message": message,
                    "conversation_id": conversation_id
                },
                timeout=180
            )

            response.raise_for_status()
            data = response.json()

            conversation_id = data["conversation_id"]

            print("\nBot:", data["assistant_message"]["content"])
            print("Conversation ID:", conversation_id)
            print()

        except requests.RequestException as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
