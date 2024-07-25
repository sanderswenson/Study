from abc import ABC, abstractmethod
import aiohttp
import asyncio
from typing import Dict, Any

class AIProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str, system_content: str) -> str:
        pass

class OpenAIProvider(AIProvider):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.semaphore = asyncio.Semaphore(config['rate_limit']['calls_per_minute'])

    async def generate_text(self, prompt: str, system_content: str) -> str:
        async with self.semaphore:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": self.config['model'],
                    "messages": [
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": self.config['max_tokens'],
                    "temperature": self.config['temperature']
                }
                for attempt in range(self.config['rate_limit']['max_retries']):
                    try:
                        async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data) as response:
                            if response.status == 200:
                                result = await response.json()
                                return result['choices'][0]['message']['content'].strip()
                            elif response.status == 429:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            else:
                                response.raise_for_status()
                    except aiohttp.ClientError as e:
                        if attempt == self.config['rate_limit']['max_retries'] - 1:
                            raise e
                        await asyncio.sleep(2 ** attempt)
                raise Exception("Max retries reached")