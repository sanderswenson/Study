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
        self.children = []

    def __repr__(self):
        return f"{self.number} {self.name}"

def parse_md_tasks(md_file):
    with open(md_file, 'r') as f:
        lines = f.read().split('\n')
    goal = lines[0].strip('# ')
    tasks = []
    for line in lines[1:]:
        if line.strip() and not line.startswith('#'):
            match = re.match(r'^(\d+(?:\.\d+)*)\. (.+)$', line.strip())
            if match:
                number, name = match.groups()
                tasks.append(Task(number, name, len(number.split('.'))))
    return goal, tasks

@sleep_and_retry
@limits(calls=config.CALLS_PER_MINUTE, period=60)
def research_task(task):
    prompt = config.RESEARCH_PROMPT.format(task=task)
    try:
        response = openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a knowledgeable research assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error researching task '{task}': {str(e)}")
        return f"Error occurred while researching this task: {str(e)}"

def write_research_to_file(task, research, output_folder):
    file_path = os.path.join(output_folder, f"{task.number} {task.name}.md")
    with open(file_path, 'w') as f:
        f.write(f"# {task.number} {task.name}\n\n{research}")

def main(input_file, output_folder):
    goal, tasks = parse_md_tasks(input_file)
    logger.info(f"Conducting research for goal: '{goal}' with {len(tasks)} tasks")
    os.makedirs(output_folder, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(research_task, str(task)) for task in tasks]
        for task, future in zip(tasks, futures):
            research = future.result()
            write_research_to_file(task, research, output_folder)

    logger.info(f"Research completed. Results written to {output_folder}")

if __name__ == "__main__":
    main(config.DEFAULT_TASKLIST_FILE, config.DEFAULT_OUTPUT_FOLDER)