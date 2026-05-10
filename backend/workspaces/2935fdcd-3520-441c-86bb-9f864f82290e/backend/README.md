
## Main Components

### Backend Components
- **FastAPI Application**: Core web server and routing
- **In-Memory Storage**: Simple dictionary-based storage for tasks
- **Task Service**: Business logic for task operations
- **API Endpoints**: RESTful endpoints for task CRUD operations
- **Pydantic Models**: Data validation and serialization

### Frontend Components
- **React Components**: Reusable UI components for tasks and filters
- **Custom Hooks**: Logic for API calls and state management
- **TypeScript Types**: Strong typing for API contracts and UI state
- **Dark UI Theme**: Modern dark-themed UI using CSS

## Data Flow
1. Frontend sends HTTP requests to backend API endpoints
2. Backend processes requests, validates data, and performs operations on in-memory storage
3. Backend returns JSON responses with task data
4. Frontend updates UI based on API responses