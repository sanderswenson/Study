from typing import List, Dict, Any
from api_handler import AIProvider

class SubTasker:
    def __init__(self, ai_provider: AIProvider):
        self.ai_provider = ai_provider

    async def expand_task(self, task: str, settings: Dict[str, Any]) -> List[str]:
        # Extract settings with default values
        num_tasks = settings.get('num_tasks', 3)
        specificity = settings.get('specificity', 'moderately detailed')
        extra_instructions = settings.get('extra_instructions', '')

        prompt = f"""
        Task: {task}

        Please break down this task into {num_tasks} {specificity} subtasks.
        {extra_instructions}

        Provide your response as a numbered list:
        1. [First subtask]
        2. [Second subtask]
        3. [Third subtask]
        ...

        Only list the subtasks without additional explanations.
        """

        system_content = "You are a helpful assistant that breaks down tasks into smaller subtasks."
        response = await self.ai_provider.generate_text(prompt, system_content)

        # Extract subtasks from the response
        subtasks = response.split('\n')
        # Remove numbering and any empty lines
        subtasks = [task.split('.', 1)[-1].strip() for task in subtasks if task.strip()]

        return subtasks

# Example usage
if __name__ == "__main__":
    import asyncio
    from api_handler import OpenAIProvider

    async def main():
        api_config = {
            "api_key": "your-openai-api-key-here",
            "model": "gpt-3.5-turbo",
            "max_tokens": 150,
            "temperature": 0.7
        }
        ai_provider = OpenAIProvider(api_config)
        subtasker = SubTasker(ai_provider)

        main_task = "Build a website"
        settings = {
            "num_tasks": 5,
            "specificity": "highly detailed",
            "extra_instructions": "Focus on technical aspects of website development."
        }

        subtasks = await subtasker.expand_task(main_task, settings)

        print(f"Main task: {main_task}")
        print("Subtasks:")
        for i, subtask in enumerate(subtasks, 1):
            print(f"{i}. {subtask}")

    asyncio.run(main())