# Real-Time Chat Application Architecture

## Folder Structure
chat_app/
├── backend/
│   ├── main.py                # FastAPI app entry point
│   ├── models.py              # Pydantic models & data structures
│   ├── schemas.py             # API request/response schemas
│   ├── services/
│   │   ├── chat_service.py    # Core chat logic
│   │   └── user_service.py    # User presence & auth
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rooms.py           # Room endpoints
│   │   └── messages.py        # Message endpoints
│   └── storage/
│       └── in_memory.py       # In-memory storage (dicts/lists)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatRoom.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── UserPresence.tsx
│   │   │   └── ThemeToggle.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── types/
│   │   │   └── api.ts         # TypeScript API types
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── README.md

## Key Components
Backend:
- FastAPI server with WebSocket support for real-time updates
- In-memory storage for users, rooms, and messages
- Separate services for chat logic and user presence
- Pydantic models for data validation

Frontend:
- React 18 with TypeScript
- WebSocket hook for real-time communication
- Dark theme toggle component
- Modular UI components for chat functionality