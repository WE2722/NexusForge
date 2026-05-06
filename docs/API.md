# NexusForge API Documentation

## Endpoints

### Projects
- `POST /api/projects` - Create a new project. Expects `{"prompt": "string"}`.
- `GET /api/projects` - List all projects.
- `GET /api/projects/{id}` - Get project details.
- `GET /api/projects/{id}/stream` - SSE endpoint for live updates.
- `POST /api/projects/{id}/pause` - Pause execution.
- `POST /api/projects/{id}/resume` - Resume execution.

### Agents
- `GET /api/agents` - List available agents and their capabilities.

### System
- `GET /api/health` - System health check.
