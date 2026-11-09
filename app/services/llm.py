import os
import json
import requests

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/chat"
)

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def prepare_gemini_messages(messages: list[dict]):
    system_prompt = ""
    contents = []

    for message in messages:
        role = message["role"]
        content = message["content"]

        if role == "system":
            system_prompt = content
        else:
            gemini_role = "model" if role == "assistant" else "user"

            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=content)]
                )
            )

    return system_prompt, contents


def generate_response(messages: list[dict]):

    # Provider 1: Ollama
    if LLM_PROVIDER == "ollama":

        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False
        }

        try:
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=180
            )
            response.raise_for_status()

            result = response.json()

            prompt_tokens = result.get("prompt_eval_count", 0)
            completion_tokens = result.get("eval_count", 0)

            return {
                "content": result["message"]["content"],
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Ollama error: {error}"
            ) from error

    # Provider 2: Gemini
    elif LLM_PROVIDER == "gemini":

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing from .env")

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            system_prompt, contents = prepare_gemini_messages(messages)

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )

            usage = response.usage_metadata

            prompt_tokens = usage.prompt_token_count if usage else 0
            completion_tokens = usage.candidates_token_count if usage else 0
            total_tokens = usage.total_token_count if usage else 0

            return {
                "content": response.text or "",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }

        except Exception as error:
            raise RuntimeError(
                f"Gemini API error: {error}"
            ) from error

    else:
        raise ValueError(
            f"Unsupported LLM provider: {LLM_PROVIDER}"
        )


def generate_streaming_response(messages: list[dict]):

    # Provider 1: Ollama
    if LLM_PROVIDER == "ollama":

        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": True
        }

        try:
            with requests.post(
                OLLAMA_URL,
                json=payload,
                stream=True,
                timeout=(10, 180)
            ) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)

                        content = data.get(
                            "message", {}
                        ).get("content", "")

                        if content:
                            yield {"content": content}

                        if data.get("done"):
                            prompt_tokens = data.get(
                                "prompt_eval_count", 0
                            )
                            completion_tokens = data.get(
                                "eval_count", 0
                            )

                            yield {
                                "usage": {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": (
                                        prompt_tokens + completion_tokens
                                    )
                                }
                            }

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Ollama streaming error: {error}"
            ) from error

    # Provider 2: Gemini
    elif LLM_PROVIDER == "gemini":

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing from .env")

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            system_prompt, contents = prepare_gemini_messages(messages)

            response_stream = client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )

            latest_usage = None

            for chunk in response_stream:

                if chunk.text:
                    yield {"content": chunk.text}

                if chunk.usage_metadata:
                    latest_usage = chunk.usage_metadata

            if latest_usage:
                yield {
                    "usage": {
                        "prompt_tokens": (
                            latest_usage.prompt_token_count or 0
                        ),
                        "completion_tokens": (
                            latest_usage.candidates_token_count or 0
                        ),
                        "total_tokens": (
                            latest_usage.total_token_count or 0
                        )
                    }
                }

        except Exception as error:
            raise RuntimeError(
                f"Gemini streaming error: {error}"
            ) from error

    else:
        raise ValueError(
            f"Unsupported LLM provider: {LLM_PROVIDER}"
        )
