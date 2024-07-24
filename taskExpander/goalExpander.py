import openai
import os
import time
import argparse
import logging
from dotenv import load_dotenv
import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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

def parse_response(response):
    return [line.split('.', 1)[-1].strip() for line in response.split('\n') if line.strip()]

def expand_task(task, current_depth=0):
    if current_depth >= config.MAX_DEPTH:
        logger.info(f"Reached max depth for task: {task}")
        return {"task": task, "sub_tasks": []}
    
    logger.info(f"Expanding task: '{task}' at depth {current_depth}")
    prompt = create_prompt(task, current_depth, config.MAX_DEPTH)
    
    for attempt in range(config.MAX_RETRIES):
        try:
            response = openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional project manager with expertise in task breakdown and organization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.MAX_TOKENS,
                n=1,
                temperature=config.TEMPERATURE,
            )
            sub_tasks = parse_response(response.choices[0].message.content.strip())
            logger.info(f"Successfully expanded task: '{task}' into {len(sub_tasks)} sub-tasks")
            break
        except openai.error.RateLimitError:
            logger.warning(f"Rate limit reached. Attempt {attempt + 1} of {config.MAX_RETRIES}.")
            if attempt < config.MAX_RETRIES - 1:
                time.sleep(20)
            else:
                logger.error(f"Rate limit persisted. Unable to expand task: {task}")
                return {"task": task, "sub_tasks": []}
        except Exception as e:
            logger.error(f"Error expanding task '{task}': {str(e)}")
            return {"task": task, "sub_tasks": []}
    
    expanded_sub_tasks = [expand_task(sub_task, current_depth + 1) for sub_task in sub_tasks]
    return {"task": task, "sub_tasks": expanded_sub_tasks}

def write_task_list_to_md(task_list, file, indent=0, parent_number=''):
    for i, task in enumerate(task_list, 1):
        current_number = f"{parent_number}{i}." if parent_number else f"{i}."
        if isinstance(task, dict):
            file.write(f"{'    ' * indent}{current_number} {task['task']}\n")
            if task['sub_tasks']:
                write_task_list_to_md(task['sub_tasks'], file, indent + 1, current_number)
        else:
            file.write(f"{'    ' * indent}{current_number} {task}\n")

def count_tasks(task_list):
    return len(task_list) + sum(count_tasks(task['sub_tasks']) for task in task_list if isinstance(task['sub_tasks'], list))

def main(goal, output_file):
    logger.info(f"Starting task expansion for goal: '{goal}' with max depth of {config.MAX_DEPTH}")
    
    expanded_tasks = expand_task(goal)
    
    logger.info(f"Task expansion completed. Writing results to {output_file}")
    with open(output_file, 'w') as f:
        f.write(f"# {goal}\n\n")
        write_task_list_to_md([expanded_tasks], f)
        
        total_subtasks = count_tasks([expanded_tasks]) - 1
        f.write(f"\n## Summary\n\n")
        f.write(f"- Goal: {goal}\n")
        f.write(f"- Total subtasks: {total_subtasks}\n")
        f.write(f"- Maximum depth: {config.MAX_DEPTH}\n")
    
    logger.info(f"Task list has been exported to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand tasks from a goal and export to Markdown")
    parser.add_argument("--max-depth", type=int, default=config.MAX_DEPTH, help="Maximum depth for task expansion")
    parser.add_argument("--output", default=config.DEFAULT_TASKLIST_FILE, help="Output file name")
    parser.add_argument("--goal", default=config.DEFAULT_GOAL, help="The main goal to expand into tasks")
    args = parser.parse_args()

    config.MAX_DEPTH = args.max_depth
    main(args.goal, args.output)