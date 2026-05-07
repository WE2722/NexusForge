from api.v1.endpoints import todos
todos.test_func()

from app.models.schemas import schemas
# wait, if we have schemas.py:
import schemas
schemas.test_func = todos.test_func
schemas.test_func()
