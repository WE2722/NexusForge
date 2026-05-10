# Real-Time Chat Application - Architecture Overview

## Folder Structure

chat_app/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── rooms.py    # Chat room endpoints
│   │   │   ├── messages.py # Message endpoints
│   │   │   └── users.py    # User endpoints
│   ├── core/
│   │   ├── config.py        # Application configuration
│   │   └── security.py      # Authentication utilities
│   ├── models/
│   │   ├── room.py          # Room data model
│   │   ├── message.py       # Message data model
│   │   └── user.py          # User data model
│   ├── schemas/
│   │   ├── room.py          # Room Pydantic schemas
│   │   ├── message.py       # Message Pydantic schemas
│   │   └── user.py          # User Pydantic schemas
│   └── services/
│       ├── room_service.py  # Room business logic
│       ├── message_service.py # Message business logic
│       └── user_service.py  # User business logic
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatRoom.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── UserPresence.tsx
│   │   │   ├── RoomList.tsx
│   │   │   └── Navbar.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts # WebSocket connection hook
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   └── Chat.tsx
│   │   ├── types/
│   │   │   ├── room.ts
│   │   │   ├── message.ts
│   │   │   └── user.ts
│   │   ├── context/
│   │   │   └── AuthContext.tsx
│   │   ├── utils/
│   │   │   └── api.ts        # API client
│   │   ├── App.tsx
│   │   └── index.tsx
│   └── package.json
│
└── README.md