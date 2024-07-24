# OpenAI API configuration
OPENAI_MODEL = "gpt-4o-mini"
MAX_TOKENS = 500
TEMPERATURE = 0.7

# Rate limiting
MAX_RETRIES = 3
CALLS_PER_MINUTE = 50

# Output configuration
DEFAULT_TASKLIST_FILE = "tasks.md"
DEFAULT_OUTPUT_FOLDER = "research_output"
DEFAULT_GOAL = "Bake a cake"

# Depth configuration
MAX_DEPTH = 1
DEPTH_SETTINGS = [
    {"remaining_depth": 3, "specificity": "high-level", "num_tasks": "3-5"},
    {"remaining_depth": 2, "specificity": "moderately detailed", "num_tasks": "4-6"},
    {"remaining_depth": 1, "specificity": "specific and actionable", "num_tasks": "5-7"}
]

# Prompt templates
TASK_EXPANSION_PROMPT = """
Task: {task}

Break down this task into {num_tasks} {specificity} sub-tasks. Consider:

1. Each sub-task should be clear, concise, and directly related to the main task.
2. Cover all necessary aspects to complete the main task.
3. Organize sub-tasks in a logical sequence or priority order.
4. Ensure sub-tasks are appropriate for the current depth level ({current_depth} out of {max_depth}).

Provide your response as a numbered list:
1. [First sub-task]
2. [Second sub-task]
3. [Third sub-task]
...

Only list the sub-tasks without additional explanations.
"""

RESEARCH_PROMPT = """
Task: {task}

Conduct background research on this task. Consider:

1. Key concepts and theories related to the task
2. Best practices or methodologies for implementing the task
3. Potential challenges or obstacles in accomplishing the task
4. Resources or tools that might be helpful

Provide a concise summary of your findings, focusing on the most relevant and actionable information.
"""