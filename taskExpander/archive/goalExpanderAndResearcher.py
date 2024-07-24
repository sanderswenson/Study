import openai
import os
import time
import argparse
import logging
from dotenv import load_dotenv
import concurrent.futures
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY

class Task:
    def __init__(self, number, name, depth):
        self.number = number
        self.name = name
        self.depth = depth
        self.children = []
        self.research = ""

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return f"{self.number} {self.name}"

def create_prompt(task, current_depth, max_depth):
    remaining_depth = max_depth - current_depth
    setting = next((s for s in config.DEPTH_SETTINGS if s['remaining_depth'] <= remaining_depth), 
                   config.DEPTH_SETTINGS[-1])
    
    return config.TASK_EXPANSION_PROMPT.format(
        task=task,
        num_tasks=setting['num_tasks'],
        specificity=setting['specificity'],
        current_depth=current_depth,
        max_depth=max_depth
    )

def call_openai_api(prompt, system_content):
    for attempt in range(config.MAX_RETRIES):
        try:
            response = openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.MAX_TOKENS,
                n=1,
                temperature=config.TEMPERATURE,
            )
            return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            if attempt < config.MAX_RETRIES - 1:
                time.sleep(20)
            else:
                logger.error("Rate limit reached. Unable to process task.")
                return "Error: Rate limit reached while processing this task."
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return f"Error occurred while processing this task: {str(e)}"

def expand_task(task, current_depth=0):
    if current_depth >= config.MAX_DEPTH:
        logger.info(f"Reached max depth for task: {task}")
        return Task(str(current_depth + 1), task, current_depth)
    
    logger.info(f"Expanding task: '{task}' at depth {current_depth}")
    prompt = create_prompt(task, current_depth, config.MAX_DEPTH)
    
    response = call_openai_api(prompt, "You are a professional project manager with expertise in task breakdown and organization.")
    sub_tasks = [line.split('.', 1)[-1].strip() for line in response.split('\n') if line.strip()]
    
    current_task = Task(str(current_depth + 1), task, current_depth)
    for i, sub_task in enumerate(sub_tasks, 1):
        child_task = expand_task(sub_task, current_depth + 1)
        child_task.number = f"{current_task.number}.{i}"
        current_task.add_child(child_task)
    
    return current_task

def research_task(task):
    prompt = config.RESEARCH_PROMPT.format(task=task)
    return call_openai_api(prompt, "You are a knowledgeable research assistant with expertise in various fields.")

def process_task(task, base_path):
    current_path = base_path
    for i in range(1, task.depth + 1):
        folder_name = f"{'.'.join(task.number.split('.')[:i])}"
        if i == task.depth:
            folder_name += f" {task.name}"
        current_path = os.path.join(current_path, folder_name)
        os.makedirs(current_path, exist_ok=True)
    
    file_name = f"{task.number} {task.name}.md"
    file_path = os.path.join(current_path, file_name)
    
    task.research = research_task(str(task))
    
    with open(file_path, 'w') as f:
        f.write(f"# {task.number} {task.name}\n\n")
        f.write(task.research)
        if task.children:
            f.write("\n\n## Subtasks\n\n")
            for child in task.children:
                f.write(f"- [{child.number} {child.name}]({child.number} {child.name}.md)\n")
    
    return task

def main(goal, output_folder):
    logger.info(f"Starting task expansion and research for goal: '{goal}'")
    
    root_task = expand_task(goal)
    
    all_tasks = []
    def flatten_tasks(task):
        all_tasks.append(task)
        for child in task.children:
            flatten_tasks(child)
    
    flatten_tasks(root_task)
    
    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, "goal.md"), 'w') as f:
        f.write(f"# {goal}\n\n")
        for child in root_task.children:
            f.write(f"- [{child.number} {child.name}]({child.number} {child.name}/{child.number} {child.name}.md)\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_task = {executor.submit(process_task, task, output_folder): task for task in all_tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            try:
                future.result()
            except Exception as exc:
                logger.error(f'{task} generated an exception: {exc}')

    logger.info(f"Task expansion and research completed. Results written to folder structure in {output_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand tasks, conduct research, and create folder structure")
    parser.add_argument("--goal", required=True, help="The main goal to expand into tasks and research")
    parser.add_argument("--output", default=config.DEFAULT_OUTPUT_FOLDER, help="Output folder for results")
    args = parser.parse_args()

    main(args.goal, args.output)