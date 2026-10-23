import os
import time
from typing import Type, TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import errors

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Default fallback jika tidak ada di .env
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")
        self.client = genai.Client(api_key=self.api_key)

    def _call_with_retry(self, fn, *args, **kwargs):
        """Menangani server kelebihan beban (503 UNAVAILABLE / 429 RATE LIMIT) secara otomatis."""
        max_retries = 5
        delay = 4
        for attempt in range(max_retries):
            try:
                return fn(*args, **kwargs)
            except errors.ServerError as e:
                # 503 Service Unavailable / Model High Demand
                if attempt == max_retries - 1:
                    raise e
                time.sleep(delay)
                delay *= 2  # Exponential backoff: 4s -> 8s -> 16s -> 32s
            except errors.ClientError as e:
                # Menangani batas laju request jika terkena status 429
                if getattr(e, "code", None) == 429 and attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise e

    def generate_structured(self, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        for attempt in range(3):
            try:
                response = self._call_with_retry(
                    self.client.models.generate_content,
                    model=self.model_name,
                    contents=user_prompt,
                    config={
                        "system_instruction": system_prompt,
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                        "temperature": 0.2,
                    }
                )
                return schema.model_validate_json(response.text)
            except Exception as e:
                if attempt == 2:
                    raise ValueError(f"Gagal generate respons terstruktur setelah 3 percobaan: {e}")
                time.sleep(2)
                user_prompt += f"\nPerbaiki format output JSON sebelumnya yang mengalami error: {str(e)}"

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._call_with_retry(
            self.client.models.generate_content,
            model=self.model_name,
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "temperature": 0.3,
            }
        )
        return response.text