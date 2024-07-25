import yaml
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Load and parse the YAML configuration file."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)