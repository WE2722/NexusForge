import json
import sqlite3

def patch_db():
    conn = sqlite3.connect('c:/Users/Wiam/Desktop/S8/NexusForge/backend/nexusforge.db')
    cursor = conn.cursor()
    
    # Get all task results
    cursor.execute("SELECT id, result FROM tasks WHERE agent_type IN ('backend', 'frontend')")
    tasks = cursor.fetchall()
    
    for task_id, result_str in tasks:
        if not result_str:
            continue
            
        try:
            result = json.loads(result_str)
            modified = False
            
            if 'code_blocks' in result:
                # Fix frontend package.json
                for key in list(result['code_blocks'].keys()):
                    if key.endswith('package.json'):
                        content = result['code_blocks'][key]
                        if '//' in content:
                            import re
                            content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)
                            result['code_blocks'][key] = content
                            modified = True
                            
                # Fix backend main.py
                for key in list(result['code_blocks'].keys()):
                    if key.endswith('main.py'):
                        content = result['code_blocks'][key]
                        if 'if settings' in content and 'if settings:' not in content:
                            content = content.replace('if settings\n', 'if settings:\n')
                            result['code_blocks'][key] = content
                            modified = True
                            
            if modified:
                cursor.execute("UPDATE tasks SET result = ? WHERE id = ?", (json.dumps(result), task_id))
                print(f"Patched task {task_id}")
                
        except Exception as e:
            print(f"Error parsing task {task_id}: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    patch_db()
