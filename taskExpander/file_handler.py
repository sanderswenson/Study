import os
from typing import Dict, Any
from task_expander import Task

class FileHandler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def write_task_list(self, task: Task, file_path: str = None):
        if file_path is None:
            file_path = self.config['task_list_file']
        
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w') as f:
            self._write_task(task, f)

    def _write_task(self, task: Task, file, indent: int = 0):
        file.write(f"{'  ' * indent}- {task.name}\n")
        for sub_task in task.sub_tasks:
            self._write_task(sub_task, file, indent + 1)

    async def write_research(self, task: Task, research: str):
        folder = self.config['research_folder']
        os.makedirs(folder, exist_ok=True)
        
        file_name = f"{task.name.replace(' ', '_')}.md"
        file_path = os.path.join(folder, file_name)
        
        with open(file_path, 'w') as f:
            f.write(f"# {task.name}\n\n{research}\n")