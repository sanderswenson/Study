import openai
import os
import logging
from dotenv import load_dotenv
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def create_prompt(task, current_depth, max_depth):
    remaining_depth = max_depth - current_depth
    setting = next((s for s in config.DEPTH_SETTINGS if s['remaining_depth'] <= remaining_depth), 
                   config.DEPTH_SETTINGS[-1])
    return config.TASK_EXPANSION_PROMPT.format(
        task=task, num_tasks=setting['num_tasks'], specificity=setting['specificity'],
        current_depth=current_depth, max_depth=max_depth
    )

def expand_task(task, current_depth=0):
    if current_depth >= config.MAX_DEPTH:
        return {"task": task, "sub_tasks": []}
    
    logger.info(f"Expanding task: '{task}' at depth {current_depth}")
    prompt = create_prompt(task, current_depth, config.MAX_DEPTH)
    
    try:
        response = openai.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional project manager with expertise in task breakdown."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )
        sub_tasks = [line.split('.', 1)[-1].strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
        return {"task": task, "sub_tasks": [expand_task(sub_task, current_depth + 1) for sub_task in sub_tasks]}
    except Exception as e:
        logger.error(f"Error expanding task '{task}': {str(e)}")
        return {"task": task, "sub_tasks": []}

def write_task_list_to_md(task_list, file, indent=0, parent_number=''):
    for i, task in enumerate(task_list, 1):
        current_number = f"{parent_number}{i}." if parent_number else f"{i}."
        file.write(f"{'    ' * indent}{current_number} {task['task']}\n")
        if task['sub_tasks']:
            write_task_list_to_md(task['sub_tasks'], file, indent + 1, current_number)

def main(goal, output_file):
    logger.info(f"Starting task expansion for goal: '{goal}' with max depth of {config.MAX_DEPTH}")
    expanded_tasks = expand_task(goal)
    
    with open(output_file, 'w') as f:
        f.write(f"# {goal}\n\n")
        write_task_list_to_md([expanded_tasks], f)
    
    logger.info(f"Task list has been exported to {output_file}")

if __name__ == "__main__":
    main(config.DEFAULT_GOAL, config.DEFAULT_TASKLIST_FILE)