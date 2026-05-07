import urllib.request
import json
req = urllib.request.Request('http://127.0.0.1:8000/api/projects')
response = urllib.request.urlopen(req)
projects = json.loads(response.read())
# get the MOST RECENT project
project_id = sorted(projects, key=lambda x: x['created_at'], reverse=True)[0]['id']
req2 = urllib.request.Request(f'http://127.0.0.1:8000/api/projects/{project_id}')
response2 = urllib.request.urlopen(req2)
proj = json.loads(response2.read())
back_task = next(t for t in proj['tasks'] if t['agent_type'] == 'backend')
keys = list(back_task.get('result', {}).get('code_blocks', {}).keys())
print("BACKEND KEYS:", keys)
for k, v in back_task['result']['code_blocks'].items():
    if k.endswith('main.py'):
        print(f"--- {k} ---")
        print(v[:500])
