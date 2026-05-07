import asyncio
from app.services.orchestrator import Orchestrator

async def test_orchestrator():
    orchestrator = Orchestrator()
    prompt = "Build a Todo List application with React and FastAPI."
    project = await orchestrator.create_project(prompt)
    print("Project status:", project.status)
    for task in project.tasks:
        print(f"Task {task.agent_type}: {task.status}")
        if task.status == 'failed':
            print("  Result:", task.result)
            print("  Attempts:", task.attempts)

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
