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
for k, v in back_task['result']['code_blocks'].items():
    print(f"--- {k} ---")
