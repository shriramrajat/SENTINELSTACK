from typing import Protocol, Dict
import httpx
import json
import random

class LLMProvider(Protocol):
    """
    Interface for any LLM Backend (OpenAI, Gemini, Ollama, Mock)
    """
    async def generate_insight(self, system_prompt: str, context_data: Dict) -> Dict:
        ...

class MockLLM:
    """
    Cost-free, instant responses for dev/test environments.
    Simulates AI reasoning based on simple heuristics, but returns structured JSON.
    """
    async def generate_insight(self, system_prompt: str, context_data: Dict) -> Dict:
        error_count = sum(item['count'] for item in context_data.get('errors', []))
        
        if error_count == 0:
            return {
                "summary": "Systems Operating Normally",
                "analysis": "No anomalies detected in the last 15 minutes. Traffic patterns are stable.",
                "action_items": ["Monitor standard metrics", "Check planned maintenance schedule"],
                "severity": "low"
            }
        
        # Simulate "AI Analysis"
        return {
            "summary": f"Elevated Error Rate Detected ({error_count} events)",
            "analysis": "Traffic analysis indicates a spike in 500 errors on the /payment endpoint. This strongly correlates with the recent deployment window.",
            "action_items": [
                "Rollback latest deployment if error rate persists > 2%",
                "Check database connection pool status",
                "Verify third-party payment gateway status page"
            ],
            "severity": "critical" if error_count > 50 else "medium"
        }

class OpenAI_LLM:
    """
    Production-grade LLM integration.
    Requires OPENAI_API_KEY env var.
    """
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"

    async def generate_insight(self, system_prompt: str, context_data: Dict) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(context_data, indent=2)}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            except Exception as e:
                # Fallback to a safe error message if LLM fails
                print(f"LLM Error: {e}")
                return {
                    "summary": "AI Service Temporarily Unavailable",
                    "analysis": "Could not contact LLM provider.",
                    "action_items": ["Check API Keys", "Check Internet Connection"],
                    "severity": "unknown"
                }

# Factory
def get_llm_provider(env: str = "dev", api_key: str = "") -> LLMProvider:
    if env == "prod" and api_key:
        return OpenAI_LLM(api_key)
    return MockLLM()
