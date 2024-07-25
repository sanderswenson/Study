from typing import Dict, Any, List
from api_handler import AIProvider

class Task:
    def __init__(self, name: str, depth: int):
        self.name = name
        self.depth = depth
        self.sub_tasks: List[Task] = []

    def __repr__(self):
        return f"Task(name='{self.name}', depth={self.depth}, sub_tasks={len(self.sub_tasks)})"

class TaskExpander:
    def __init__(self, ai_provider: AIProvider, config: Dict[str, Any]):
        self.ai_provider = ai_provider
        self.config = config

    async def expand_task(self, task: Task) -> Task:
        if task.depth >= self.config['max_depth']:
            return task

        setting = next(s for s in self.config['depth_settings'] if s['remaining_depth'] <= self.config['max_depth'] - task.depth)
        prompt = self.config['prompt_template'].format(
            task=task.name,
            num_tasks=setting['num_tasks'],
            specificity=setting['specificity'],
            current_depth=task.depth,
            max_depth=self.config['max_depth']
        )

        response = await self.ai_provider.generate_text(prompt, "You are a professional project manager with expertise in task breakdown.")
        sub_tasks = [line.split('.', 1)[-1].strip() for line in response.split('\n') if line.strip()]

        for sub_task in sub_tasks:
            expanded_sub_task = Task(sub_task, task.depth + 1)
            task.sub_tasks.append(await self.expand_task(expanded_sub_task))

        return task