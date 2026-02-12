from dotenv import load_dotenv
load_dotenv()

from openai import AsyncOpenAI

class LLMClient:
    def __init__(self, model="gpt-4o-mini"):
        self.client = AsyncOpenAI()
        self.model = model

    async def run(self, prompt: str):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
