import openai
import os
import logging
from dotenv import load_dotenv
import re
import concurrent.futures
from ratelimit import limits, sleep_and_retry
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class Task:
    def __init__(self, number, name, depth):
        self.number, self.name, self.depth = number, name, depth
        self.sub_tasks = []

    def __repr__(self):
        return f"{self.number} {self.name}"

def create_prompt(task, current_depth, max_depth, prompt_type):
    if prompt_type == "expansion":
        remaining_depth = max_depth - current_depth
        setting = next((s for s in config.DEPTH_SETTINGS if s['remaining_depth'] <= remaining_depth), 
                       config.DEPTH_SETTINGS[-1])
        return config.TASK_EXPANSION_PROMPT.format(
            task=task, num_tasks=setting['num_tasks'], specificity=setting['specificity'],
            current_depth=current_depth, max_depth=max_depth
        )
    elif prompt_type == "research":
        return config.RESEARCH_PROMPT.format(task=task)

@sleep_and_retry
@limits(calls=config.CALLS_PER_MINUTE, period=60)
def call_openai_api(prompt, system_content):
    try:
        response = openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return f"Error occurred: {str(e)}"

def expand_task(task, current_depth=0):
    if current_depth >= config.MAX_DEPTH:
        return Task(task.number, task.name, current_depth)
    
    logger.info(f"Expanding task: '{task}' at depth {current_depth}")
    prompt = create_prompt(task.name, current_depth, config.MAX_DEPTH, "expansion")
    
    response = call_openai_api(prompt, "You are a professional project manager with expertise in task breakdown.")
    sub_tasks = [line.split('.', 1)[-1].strip() for line in response.split('\n') if line.strip()]
    
    expanded_task = Task(task.number, task.name, current_depth)
    for i, sub_task in enumerate(sub_tasks, 1):
        sub_number = f"{task.number}{i}." if task.number else f"{i}."
        expanded_sub_task = expand_task(Task(sub_number, sub_task, current_depth + 1), current_depth + 1)
        expanded_task.sub_tasks.append(expanded_sub_task)
    
    return expanded_task

def research_task(task):
    prompt = create_prompt(str(task), 0, 0, "research")
    return call_openai_api(prompt, "You are a knowledgeable research assistant.")

def write_task_list_to_md(task, file, indent=0):
    file.write(f"{'    ' * indent}{task.number} {task.name}\n")
    for sub_task in task.sub_tasks:
        write_task_list_to_md(sub_task, file, indent + 1)

def write_research_to_file(task, research, output_folder):
    file_path = os.path.join(output_folder, f"{task.number} {task.name}.md")
    with open(file_path, 'w') as f:
        f.write(f"# {task.number} {task.name}\n\n{research}")

def expand_goal(goal, output_file):
    logger.info(f"Starting task expansion for goal: '{goal}' with max depth of {config.MAX_DEPTH}")
    expanded_tasks = expand_task(Task("", goal, 0))
    
    with open(output_file, 'w') as f:
        f.write(f"# {goal}\n\n")
        write_task_list_to_md(expanded_tasks, f)
    
    logger.info(f"Task list has been exported to {output_file}")
    return expanded_tasks

def research_tasks(tasks, output_folder):
    logger.info(f"Conducting research for {len(tasks)} tasks")
    os.makedirs(output_folder, exist_ok=True)

    def process_task(task):
        research = research_task(task)
        write_research_to_file(task, research, output_folder)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(process_task, tasks))

    logger.info(f"Research completed. Results written to {output_folder}")

def flatten_tasks(task):
    yield task
    for sub_task in task.sub_tasks:
        yield from flatten_tasks(sub_task)

def main(goal, tasklist_file, research_folder):
    expanded_tasks = expand_goal(goal, tasklist_file)
    all_tasks = list(flatten_tasks(expanded_tasks))
    research_tasks(all_tasks, research_folder)

if __name__ == "__main__":
    main(config.DEFAULT_GOAL, config.DEFAULT_TASKLIST_FILE, config.DEFAULT_OUTPUT_FOLDER)