import json
from app.models.schemas import Project

p = Project(raw_prompt="test", status="pending")
try:
    data = p.model_dump(mode='json')
    print("DUMP OK")
    json.dumps(data)
    print("JSON OK")
except Exception as e:
    import traceback
    traceback.print_exc()
