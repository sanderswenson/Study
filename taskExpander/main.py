import asyncio
import click
from typing import Dict, Any
from config_parser import load_config
from api_handler import OpenAIProvider
from task_expander import TaskExpander, Task
from task_researcher import TaskResearcher
from file_handler import FileHandler

async def process_task(task: Task, researcher: TaskResearcher, file_handler: FileHandler):
    research = await researcher.research_task(task)
    await file_handler.write_research(task, research)
    click.echo(f"Completed research for: {task.name}")
    
    for sub_task in task.sub_tasks:
        await process_task(sub_task, researcher, file_handler)

@click.command()
@click.option('--config', default='config.yaml', help='Path to config file')
@click.option('--goal', prompt='Enter your goal', help='The main goal to expand and research')
def main(config: str, goal: str):
    asyncio.run(async_main(config, goal))

async def async_main(config_path: str, goal: str):
    config_data: Dict[str, Any] = load_config(config_path)
    
    ai_provider = OpenAIProvider(config_data['api'])
    expander = TaskExpander(ai_provider, config_data['expansion'])
    researcher = TaskResearcher(ai_provider, config_data['research'])
    file_handler = FileHandler(config_data['output'])

    root_task = Task(goal, 0)
    expanded_task = await expander.expand_task(root_task)
    
    await file_handler.write_task_list(expanded_task)
    click.echo("Task list written to file.")

    await process_task(expanded_task, researcher, file_handler)
    click.echo("Research completed for all tasks.")

if __name__ == '__main__':
    main()