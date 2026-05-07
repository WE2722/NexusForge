import urllib.request
import json
req = urllib.request.Request('http://127.0.0.1:8000/api/projects')
response = urllib.request.urlopen(req)
projects = json.loads(response.read())
project_id = projects[0]['id']
req2 = urllib.request.Request(f'http://127.0.0.1:8000/api/projects/{project_id}')
response2 = urllib.request.urlopen(req2)
proj = json.loads(response2.read())
front_task = next(t for t in proj['tasks'] if t['agent_type'] == 'frontend')
keys = list(front_task.get('result', {}).get('code_blocks', {}).keys())
print("FRONTEND KEYS:", keys)
