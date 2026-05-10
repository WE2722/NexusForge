"""Frontend Agent — React/TypeScript specialist."""
from __future__ import annotations
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert React and TypeScript frontend developer.
Generate COMPLETE, WORKING frontend code that can run immediately with react-scripts.

STRICT FILE STRUCTURE RULES (you MUST follow these exactly):
1. ALL files go FLAT in the `src/` directory — NO subdirectories like components/, styles/, hooks/, utils/, etc.
2. The entry point MUST be named `index.tsx` (NOT main.tsx, NOT App.tsx as entry).
3. `index.tsx` must render `<App />` into `document.getElementById('root')`.
4. The main component file must be named `App.tsx`.
5. ALL other components go as separate files directly in `src/` (e.g., `src/TodoList.tsx`, `src/Header.tsx`).
6. CSS must be in a single file: `src/App.css` — imported in App.tsx.

STRICT CODE RULES:
1. Use functional components with hooks (useState, useEffect, etc.) — NO class components.
2. ALL TypeScript interfaces MUST use `export interface` (not just `interface`).
3. ALL imports must be flat: `import TodoList from './TodoList'` — NEVER `./components/TodoList`.
4. Use `fetch()` for API calls to `http://localhost:8008` (the backend port).
5. Handle loading and error states.
6. Make the UI beautiful with a dark theme, modern design, smooth animations.
7. Do NOT import from 'react-router-dom' unless the app genuinely needs multiple pages.
8. Do NOT use Vite-specific APIs.

STRICT OUTPUT FORMAT:
Every file must be in a labeled code block:

```tsx index.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(<React.StrictMode><App /></React.StrictMode>);
```

```tsx App.tsx
import React, { useState } from 'react';
import './App.css';
...
```

```css App.css
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0a; color: #ededed; font-family: 'Inter', sans-serif; }
...
```

Generate ALL files needed for a complete, beautiful, working frontend."""


class FrontendAgent(BaseAgent):
    name = "frontend"
    role = "Frontend Developer"
    agent_type = AgentType.FRONTEND
    expertise = ["React 18", "TypeScript", "CSS", "Responsive Design"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.GROQ]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")
        prompt = f"""Project: {task.title}

Description: {task.description}

{f'Backend API context (match these endpoints and types exactly):{chr(10)}{context}' if context else ''}

Generate the COMPLETE frontend code. Remember:
- ALL files flat in src/ (no subdirectories)
- Entry point: index.tsx (NOT main.tsx)
- Main component: App.tsx
- Single CSS file: App.css
- All interfaces must use `export interface`
- All imports flat: `./ComponentName`
- Use fetch() to call backend at http://localhost:8008
- Beautiful dark theme UI with animations
- Handle loading and error states"""
        response = await self._call_llm(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=8192)
        elapsed = (time.perf_counter() - start) * 1000
        if not response.success:
            return self._build_result(task, False, "", errors=[response.error], execution_time_ms=elapsed)
        code_blocks = self._extract_code_blocks(response.content)
        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()), reasoning="Generated frontend components",
            execution_time_ms=elapsed,
        )