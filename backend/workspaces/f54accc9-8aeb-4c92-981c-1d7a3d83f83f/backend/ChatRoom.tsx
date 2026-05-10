// Fixed: Added missing ChatRoom.css import and fixed API endpoint port
import React, { useState, useEffect } from 'react';
import './ChatRoom.css';
import { Message, User, RoomWithParticipants } from '../types/api';
import { useWebSocket } from '../hooks/useWebSocket';

interface ChatRoomProps {
  room: RoomWithParticipants;
  currentUserId: string;
}

export const ChatRoom: React.FC<ChatRoomProps> = ({ room, currentUserId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const { messages: wsMessages, presenceUpdates, sendMessage } = useWebSocket(currentUserId);

  useEffect(() => {
    // Fetch initial messages
    const fetchMessages = async () => {
      const response = await fetch(`http://localhost:8000/api/messages/${room.room.id}`);
      const data = await response.json();
      setMessages(data);
    };
    fetchMessages();
  }, [room.room.id]);

  useEffect(() => {
    // Update messages from WebSocket
    if (wsMessages.length > 0) {
      setMessages(prev => [...prev, wsMessages[wsMessages.length - 1]]);
    }
  }, [wsMessages]);

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      sendMessage(newMessage);
      setNewMessage('');
    }
  };

  return (
    <div className="chat-room">
      <div className="room-header">
        <h2>{room.room.name}</h2>
        <div className="participants">
          {room.participants.map(user => (
            <div key={user.id} className="participant">
              {user.username} {presenceUpdates[user.id] ? '🟢' : '🔴'}
            </div>
          ))}
        </div>
      </div>
      <div className="message-list">
        {messages.map(msg => (
          <div key={msg.id} className={`message ${msg.senderId === currentUserId ? 'sent' : 'received'}`}>
            <strong>{msg.senderName}:</strong> {msg.content}
          </div>
        ))}
      </div>
      <div className="message-input">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
        />
        <button onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );
};

export default ChatRoom;