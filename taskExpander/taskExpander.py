import openai
import os
import time
import argparse
import logging
from dotenv import load_dotenv
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEPTH_CONFIG = {
    'max_depth': 3,
    'depth_settings': [
        {'remaining_depth': 3, 'specificity': 'high-level', 'num_tasks': '3-5'},
        {'remaining_depth': 2, 'specificity': 'moderately detailed', 'num_tasks': '4-6'},
        {'remaining_depth': 1, 'specificity': 'specific and actionable', 'num_tasks': '5-7'}
    ]
}

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def create_prompt(task, current_depth, max_depth):
    remaining_depth = max_depth - current_depth
    setting = next((s for s in DEPTH_CONFIG['depth_settings'] if s['remaining_depth'] <= remaining_depth), 
                   DEPTH_CONFIG['depth_settings'][-1])
    
    return f"""Task: {task}

Break down this task into {setting['num_tasks']} {setting['specificity']} sub-tasks. Consider:

1. Each sub-task should be clear, concise, and directly related to the main task.
2. Cover all necessary aspects to complete the main task.
3. Organize sub-tasks in a logical sequence or priority order.
4. Ensure sub-tasks are appropriate for the current depth level ({current_depth} out of {max_depth}).

Provide your response as a numbered list:
1. [First sub-task]
2. [Second sub-task]
3. [Third sub-task]
...

Only list the sub-tasks without additional explanations."""

def parse_response(response):
    return [line.split('.', 1)[-1].strip() for line in response.split('\n') if line.strip()]

def expand_task(task, current_depth=0):
    max_depth = DEPTH_CONFIG['max_depth']
    if current_depth >= max_depth:
        logger.info(f"Reached max depth for task: {task}")
        return {"task": task, "sub_tasks": []}
    
    logger.info(f"Expanding task: '{task}' at depth {current_depth}")
    prompt = create_prompt(task, current_depth, max_depth)
    
    for attempt in range(3):
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional project manager with expertise in task breakdown and organization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                n=1,
                temperature=0.7,
            )
            sub_tasks = parse_response(response.choices[0].message.content.strip())
            logger.info(f"Successfully expanded task: '{task}' into {len(sub_tasks)} sub-tasks")
            break
        except openai.error.RateLimitError:
            logger.warning(f"Rate limit reached. Attempt {attempt + 1} of 3.")
            if attempt < 2:
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

def main(high_level_tasks, output_file):
    max_depth = DEPTH_CONFIG['max_depth']
    logger.info(f"Starting task expansion with {len(high_level_tasks)} high-level tasks and max depth of {max_depth}")
    expanded_tasks = []
    
    with tqdm(total=len(high_level_tasks), desc="Expanding tasks", unit="task") as pbar:
        for task in high_level_tasks:
            expanded_tasks.append(expand_task(task))
            pbar.update(1)
    
    logger.info(f"Task expansion completed. Writing results to {output_file}")
    with open(output_file, 'w') as f:
        f.write("# Expanded Task List\n\n")
        write_task_list_to_md(expanded_tasks, f)
        
        total_subtasks = count_tasks(expanded_tasks) - len(expanded_tasks)
        f.write(f"\n## Summary\n\n")
        f.write(f"- Total high-level tasks: {len(expanded_tasks)}\n")
        f.write(f"- Total subtasks: {total_subtasks}\n")
        f.write(f"- Maximum depth: {max_depth}\n")
    
    logger.info(f"Task list has been exported to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand tasks and export to Markdown")
    parser.add_argument("--max-depth", type=int, default=DEPTH_CONFIG['max_depth'], help="Maximum depth for task expansion")
    parser.add_argument("--output", default="expanded_tasks.md", help="Output file name")
    args = parser.parse_args()

    high_level_tasks = [
        "Developing a Unifying Framework for Creative Education, Active Engagement, Highly Palatable Media, Spirituality, Mindfullness, Student Driven Activity, and Inclusivity that incidentally covers the Highschool Equivlancy requirements."
    ]

    main(high_level_tasks, args.output)