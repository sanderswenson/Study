from typing import Dict, Any
from api_handler import AIProvider
from task_expander import Task

class TaskResearcher:
    def __init__(self, ai_provider: AIProvider, config: Dict[str, Any]):
        self.ai_provider = ai_provider
        self.config = config

    async def research_task(self, task: Task) -> str:
        prompt = self.config['prompt_template'].format(task=task.name)
        return await self.ai_provider.generate_text(prompt, "You are a knowledgeable research assistant.")