// Fixed: Corrected WebSocket message handling and type imports
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

export interface User {
  id: string;
  username: string;
  is_online: boolean;
  last_active: string;
}

export interface Room {
  id: string;
  name: string;
  users: string[];
}

export interface Message {
  id: string;
  room_id: string;
  user_id: strIng;
  content: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'message' | 'presence';
  message?: Message;
  user_id?: string;
  is_online?: boolean;
  last_active?: string;
}

const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<Record<string, User>>({});
  const [rooms, setRooms] = useState<Room[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageContent, setMessageContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  // Create user on app start
  useEffect(() => {
    const createUser = async () => {
      try {
        const response = await fetch('http://localhost:8008/api/v1/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: `User-${Math.floor(Math.random() * 1000)}` })
        });
        if (!response.ok) throw new Error('Failed to create user');
        const user: User = await response.json();
        setCurrentUser(user);
        setUsers(prev => ({ ...prev, [user.id]: user }));

        // Connect to WebSocket
        ws.current = new WebSocket(`ws://localhost:8008/ws/${user.id}`);
        ws.current.onopen = () => console.log('WebSocket connected');
        ws.current.onmessage = (event) => handleWebSocketMessage(event);
        ws.current.onclose = () => console.log('WebSocket disconnected');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    createUser();
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  // Fetch rooms
  useEffect(() => {
    if (!currentUser) return;

    const fetchRooms = async () => {
      try {
        const response = await fetch('http://localhost:8008/api/v1/rooms');
        if (!response.ok) throw new Error('Failed to fetch rooms');
        const roomsData: Room[] = await response.json();
        setRooms(roomsData);

        // Join first room if exists
        if (roomsData.length > 0) {
          joinRoom(roomsData[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    fetchRooms();
  }, [currentUser]);

  // Handle WebSocket messages
  const handleWebSocketMessage = (event: MessageEvent) => {
    const data: WebSocketMessage = JSON.parse(event.data);

    if (data.type === 'message' && data.message) {
      setMessages(prev => [...prev, data.message]);
    } else if (data.type === 'presence') {
      setUsers(prev => ({
        ...prev,
        [data.user_id || '']: {
          ...prev[data.user_id || ''],
          is_online: data.is_online || false,
          last_active: data.last_active || ''
        }
      }));
    }
  };

  // Join room
  const joinRoom = async (roomId: string) => {
    if (!currentUser) return;

    try {
        const joinResponse = await fetch(`http://localhost:8008/api/v1/rooms/${roomId}/join`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: currentUser.id })
        });
        if (!joinResponse.ok) throw new Error('Failed to join room');

        const roomResponse = await fetch(`http://localhost:8008/api/v1/rooms/${roomId}`);
        if (!roomResponse.ok) throw new Error('Failed to fetch room');
        const room: Room = await roomResponse.json();
        setSelectedRoom(room);

        // Fetch room messages
        const messagesResponse = await fetch(`http://localhost:8008/api/v1/rooms/${roomId}/messages`);
        if (!messagesResponse.ok) throw new Error('Failed to fetch messages');
        const messagesData: Message[] = await messagesResponse.json();
        setMessages(messagesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!currentUser || !selectedRoom || !messageContent.trim()) return;

    try {
      const response = await fetch('http://localhost:8008/api/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_id: selectedRoom.id,
          user_id: currentUser.id,
          content: messageContent
        })
      });
      if (!response.ok) throw new Error('Failed to send message');
      setMessageContent('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Connecting to chat...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Real-Time Chat</h1>
        {currentUser && (
          <div className="user-info">
            <span className="username">{currentUser.username}</span>
            <span className={`status ${currentUser.is_online ? 'online' : 'offline'}`}></span>
          </div>
        )}
      </header>

      <div className="chat-container">
        <div className="room-list">
          <h3>Rooms</h3>
          {rooms.length === 0 ? (
            <p className="empty-message">No rooms available</p>
          ) : (
            <ul>
              {rooms.map(room => (
                <li
                  key={room.id}
                  className={selectedRoom?.id === room.id ? 'active' : ''}
                  onClick={() => joinRoom(room.id)}
                >
                  {room.name} ({room.users.length})
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="message-area">
          {selectedRoom ? (
            <>
              <div className="room-header">
                <h2>{selectedRoom.name}</h2>
                <span className="room-users">{selectedRoom.users.length} users</span>
              </div>

              <div className="messages-container">
                {messages.length === 0 ? (
                  <p className="empty-message">No messages yet. Start the conversation!</p>
                ) : (
                  messages.map(message => {
                    const messageUser = users[message.user_id];
                    return (
                      <div key={message.id} className="message">
                        <div className="message-header">
                          <span className="sender">{messageUser?.username || 'Unknown'}</span>
                          <span className="timestamp">
                            {new Date(parseFloat(message.timestamp) * 1000).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="message-content">{message.content}</div>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="message-input">
                <input
                  type="text"
                  value={messageContent}
                  onChange={(e) => setMessageContent(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type a message..."
                />
                <button onClick={sendMessage}>Send</button>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a room to start chatting</p>
            </div>
          )}
        </div>

        <div className="presence-list">
          <h3>Online Users</h3>
          {Object.values(users).length === 0 ? (
            <p className="empty-message">No users online</p>
          ) : (
            <ul>
              {Object.values(users).map(user => (
                <li key={user.id}>
                  <span className="username">{user.username}</span>
                  <span className={`status ${user.is_online ? 'online' : 'offline'}`}></span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;