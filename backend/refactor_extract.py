import os
import re

AGENT_FILES = [
    "architecture_agent.py",
    "backend_agent.py",
    "database_agent.py",
    "debugger_agent.py",
    "frontend_agent.py",
    "review_agent.py"
]

def remove_extract_method(filepath):
    with open(filepath, "r") as f:
        content = f.read()
    
    # Use regex to find and remove the _extract_code_blocks method
    # It starts with @staticmethod and goes to the end of the file
    new_content = re.sub(r"\s*@staticmethod\s*def _extract_code_blocks.*", "", content, flags=re.DOTALL)
    
    with open(filepath, "w") as f:
        f.write(new_content)

for agent in AGENT_FILES:
    remove_extract_method(os.path.join("app", "agents", agent))

print("Removed static methods from agents.")
