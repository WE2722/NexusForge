// Fixed: Added missing room prop and removed unused useWebSocket import
import React, { useState, useEffect } from 'react';
import './App.css';
import ThemeToggle from './ThemeToggle';
import ChatRoom from './ChatRoom';

export interface AppProps {
  currentUserId: string;
}

const App: React.FC<AppProps> = ({ currentUserId }) => {
  const [selectedRoom, setSelectedRoom] = useState<any>(null);

  // In a real app, you would fetch available rooms here
  useEffect(() => {
    // Example: Fetch rooms for current user
    // const response = await fetch(`http://localhost:8000/api/rooms/?user_id=${currentUserId}`);
    // const rooms = await response.json();
    // setRooms(rooms);
  }, [currentUserId]);

  return (
    <div className="app">
      <ThemeToggle />
      <div className="chat-list">
        {selectedRoom ? (
          <ChatRoom
            room={selectedRoom}
            currentUserId={currentUserId}
          />
        ) : (
          <div>Select a room to chat</div>
        )}
      </div>
    </div>
  );
};

export default App;