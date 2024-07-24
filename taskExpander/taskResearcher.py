import openai
import os
import time
import argparse
import logging
from dotenv import load_dotenv
import re
import concurrent.futures
from ratelimit import limits, sleep_and_retry
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
@limits(calls=config.CALLS_PER_MINUTE, period=60)
def research_task(task):
    prompt = config.RESEARCH_PROMPT.format(task=task)

    for attempt in range(config.MAX_RETRIES):
        try:
            response = openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a knowledgeable research assistant with expertise in various fields."},
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
                logger.error(f"Rate limit reached. Unable to research task: {task}")
                return f"Error: Rate limit reached while researching this task."
        except Exception as e:
            logger.error(f"Error researching task '{task}': {str(e)}")
            return f"Error occurred while researching this task: {str(e)}"

def write_research_to_file(task, research, output_folder):
    file_name = f"{task.number} {task.name}.md"
    file_path = os.path.join(output_folder, file_name)
    
    with open(file_path, 'w') as f:
        f.write(f"# {task.number} {task.name}\n\n")
        f.write(research)
        if task.children:
            f.write("\n\n## Subtasks\n\n")
            for child in task.children:
                f.write(f"- [{child.number} {child.name}]({child.number} {child.name}.md)\n")

def process_task(task, output_folder):
    research = research_task(str(task))
    write_research_to_file(task, research, output_folder)
    return task

def main(input_file, output_folder):
    goal, tasks = parse_md_tasks(input_file)
    logger.info(f"Conducting research for goal: '{goal}' with {len(tasks)} top-level tasks")
    
    os.makedirs(output_folder, exist_ok=True)
    
    # with open(os.path.join(output_folder, "goal.md"), 'w') as f:
    #     f.write(f"# {goal}\n\n")
    #     for task in tasks:
    #         f.write(f"- [{task.number} {task.name}]({task.number} {task.name}.md)\n")

    all_tasks = []
    def flatten_tasks(task_list):
        for task in task_list:
            all_tasks.append(task)
            flatten_tasks(task.children)
    flatten_tasks(tasks)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_task = {executor.submit(process_task, task, output_folder): task for task in all_tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            try:
                future.result()
            except Exception as exc:
                logger.error(f'{task} generated an exception: {exc}')

    logger.info(f"Research completed. Results written to {output_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conduct background research on tasks and create Markdown files")
    parser.add_argument("--input", default="research_output.md", help="Input Markdown file with tasks")
    parser.add_argument("--output", default=config.DEFAULT_OUTPUT_FOLDER, help="Output folder for research results")
    args = parser.parse_args()

    main(args.input, args.output)