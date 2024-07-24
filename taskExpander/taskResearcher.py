import openai
import os
import time
import argparse
import logging
from dotenv import load_dotenv
from tqdm import tqdm
import re
import concurrent.futures
import json
from ratelimit import limits, sleep_and_retry

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Constants
MAX_RETRIES = 3
CALLS_PER_MINUTE = 50

class Task:
    def __init__(self, number, name, depth):
        self.number = number
        self.name = name
        self.depth = depth
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):
        return f"{self.number} {self.name}"

def parse_md_tasks(md_file):
    with open(md_file, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    goal = lines[0].strip('# ')
    tasks = []
    task_stack = []

    for line in lines[1:]:
        if line.strip() and not line.startswith('#'):
            match = re.match(r'^(\d+(?:\.\d+)*)\. (.+)$', line.strip())
            if match:
                number, name = match.groups()
                depth = len(number.split('.'))
                task = Task(number, name, depth)

                while task_stack and task_stack[-1].depth >= depth:
                    task_stack.pop()

                if task_stack:
                    task_stack[-1].add_child(task)
                else:
                    tasks.append(task)

                task_stack.append(task)

    return goal, tasks

@sleep_and_retry
@limits(calls=CALLS_PER_MINUTE, period=60)
def research_task(task):
    prompt = f"""Task: {task}

Conduct background research on this task. Consider:

1. Key concepts and theories related to the task
2. Best practices or methodologies for implementing the task
3. Potential challenges or obstacles in accomplishing the task
4. Resources or tools that might be helpful

Provide a concise summary of your findings, focusing on the most relevant and actionable information."""

    for attempt in range(MAX_RETRIES):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable research assistant with expertise in various fields."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                n=1,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(20)
            else:
                logger.error(f"Rate limit reached. Unable to research task: {task}")
                return f"Error: Rate limit reached while researching this task."
        except Exception as e:
            logger.error(f"Error researching task '{task}': {str(e)}")
            return f"Error occurred while researching this task: {str(e)}"

def create_folder_structure(task, base_path):
    current_path = base_path
    for i in range(1, task.depth + 1):
        folder_name = f"{'.'.join(task.number.split('.')[:i])}"
        if i == task.depth:
            folder_name += f" {task.name}"
        current_path = os.path.join(current_path, folder_name)
        os.makedirs(current_path, exist_ok=True)
    
    file_name = f"{task.number} {task.name}.md"
    return os.path.join(current_path, file_name)

def write_research_to_file(task, research, file_path):
    with open(file_path, 'w') as f:
        f.write(f"# {task.number} {task.name}\n\n")
        f.write(research)
        if task.children:
            f.write("\n\n## Subtasks\n\n")
            for child in task.children:
                f.write(f"- [{child.number} {child.name}]({child.number} {child.name}.md)\n")

def process_task(task, base_path):
    file_path = create_folder_structure(task, base_path)
    research = research_task(str(task))
    write_research_to_file(task, research, file_path)
    return task

def main(input_file, output_folder):
    goal, tasks = parse_md_tasks(input_file)
    logger.info(f"Conducting research for goal: '{goal}' with {len(tasks)} top-level tasks")
    
    os.makedirs(output_folder, exist_ok=True)
    with open(os.path.join(output_folder, "goal.md"), 'w') as f:
        f.write(f"# {goal}\n\n")
        for task in tasks:
            f.write(f"- [{task.number} {task.name}]({task.number} {task.name}/{task.number} {task.name}.md)\n")

    all_tasks = []
    def flatten_tasks(task_list):
        for task in task_list:
            all_tasks.append(task)
            flatten_tasks(task.children)
    flatten_tasks(tasks)

    with tqdm(total=len(all_tasks), desc="Researching tasks", unit="task") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_task = {executor.submit(process_task, task, output_folder): task for task in all_tasks}
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f'{task} generated an exception: {exc}')
                pbar.update(1)

    logger.info(f"Research completed. Results written to folder structure in {output_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conduct background research on tasks and create folder structure")
    parser.add_argument("--input", required=True, help="Input Markdown file with tasks")
    parser.add_argument("--output", default="research_output", help="Output folder for research results")
    args = parser.parse_args()

    main(args.input, args.output)