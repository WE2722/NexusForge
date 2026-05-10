"""Frontend Agent — React/TypeScript specialist.

CRITICAL: This agent MUST always generate package.json, vite.config.ts,
index.html, and tsconfig.json alongside the application code.
"""
from __future__ import annotations
import json
import time
from app.agents.base_agent import BaseAgent
from app.models.schemas import AgentResult, AgentType, LLMProvider, Task

SYSTEM_PROMPT = """You are an expert React and TypeScript frontend developer.
Generate COMPLETE, WORKING frontend code that can run immediately with Vite.

STRICT FILE STRUCTURE RULES (you MUST follow these exactly):
1. ALL component files go FLAT in the `src/` directory — NO subdirectories like components/, styles/, hooks/, utils/, etc.
2. The entry point MUST be named `main.tsx` (Vite standard).
3. `main.tsx` must render `<App />` into `document.getElementById('root')`.
4. The main component file must be named `App.tsx`.
5. ALL other components go as separate files directly in `src/` (e.g., `src/TodoList.tsx`, `src/Header.tsx`).
6. CSS must be in a single file: `src/App.css` — imported in App.tsx.
7. Do NOT generate package.json, vite.config.ts, index.html, or tsconfig.json — those are auto-generated.

STRICT CODE RULES:
1. Use functional components with hooks (useState, useEffect, etc.) — NO class components.
2. ALL TypeScript interfaces MUST use `export interface` (not just `interface`).
3. ALL imports must be flat: `import TodoList from './TodoList'` — NEVER `./components/TodoList`.
4. Use `fetch()` for API calls to `http://localhost:8008` (the backend port).
5. Handle loading and error states.
6. Make the UI beautiful with a dark theme, modern design, smooth animations.
7. Do NOT import from 'react-router-dom' unless the app genuinely needs multiple pages.

STRICT OUTPUT FORMAT:
Every file must be in a labeled code block:

```tsx main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
);
```

```tsx App.tsx
import { useState } from 'react';
import './App.css';
...
```

```css App.css
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0a; color: #ededed; font-family: 'Inter', sans-serif; }
...
```

Generate ALL component files needed for a complete, beautiful, working frontend."""


# Default scaffold files that every frontend project needs
DEFAULT_PACKAGE_JSON = {
    "name": "app-frontend",
    "private": True,
    "version": "1.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",
        "build": "tsc && vite build",
        "preview": "vite preview",
        "start": "vite"
    },
    "dependencies": {
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "lucide-react": "^0.460.0",
        "axios": "^1.7.0"
    },
    "devDependencies": {
        "@types/react": "^19.0.0",
        "@types/react-dom": "^19.0.0",
        "@vitejs/plugin-react": "^4.3.0",
        "typescript": "^5.6.0",
        "vite": "^6.0.0",
        "@tailwindcss/vite": "^4.0.0",
        "tailwindcss": "^4.0.0"
    }
}

DEFAULT_VITE_CONFIG = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    open: true
  }
})
"""

DEFAULT_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>App</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

DEFAULT_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
"""


class FrontendAgent(BaseAgent):
    name = "frontend"
    role = "Frontend Developer"
    agent_type = AgentType.FRONTEND
    expertise = ["React 19", "TypeScript", "Vite", "Tailwind CSS 4", "Responsive Design"]
    preferred_providers = [LLMProvider.GOOGLE, LLMProvider.GROQ]

    async def execute(self, task: Task) -> AgentResult:
        start = time.perf_counter()
        context = task.metadata.get("context", "")

        # Determine project name from task title
        project_name = task.title.replace(" ", "-").lower()[:30] if task.title else "app"

        prompt = f"""Project: {task.title}

Description: {task.description}

{f'Backend API context (match these endpoints and types exactly):{chr(10)}{context}' if context else ''}

Generate the COMPLETE frontend code. Remember:
- ALL files flat in src/ (no subdirectories)
- Entry point: main.tsx (Vite standard)
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

        # CRITICAL: Always inject scaffold files that the LLM doesn't generate
        pkg = dict(DEFAULT_PACKAGE_JSON)
        pkg["name"] = f"{project_name}-frontend"

        # Check if the LLM generated any extra dependencies we need to add
        full_code = response.content
        if "react-router-dom" in full_code:
            pkg["dependencies"]["react-router-dom"] = "^7.0.0"
        if "zustand" in full_code:
            pkg["dependencies"]["zustand"] = "^5.0.0"
        if "framer-motion" in full_code:
            pkg["dependencies"]["framer-motion"] = "^11.0.0"
        if "@tanstack/react-query" in full_code:
            pkg["dependencies"]["@tanstack/react-query"] = "^5.0.0"

        # Inject scaffold files — these ALWAYS exist
        code_blocks["package.json"] = json.dumps(pkg, indent=2)
        code_blocks["vite.config.ts"] = DEFAULT_VITE_CONFIG.strip()
        code_blocks["index.html"] = DEFAULT_INDEX_HTML.strip()
        code_blocks["tsconfig.json"] = DEFAULT_TSCONFIG.strip()

        return self._build_result(
            task, True, response.content, code_blocks=code_blocks,
            files_created=list(code_blocks.keys()),
            reasoning="Generated frontend components + scaffold files (package.json, vite.config.ts, index.html, tsconfig.json)",
            execution_time_ms=elapsed,
        )