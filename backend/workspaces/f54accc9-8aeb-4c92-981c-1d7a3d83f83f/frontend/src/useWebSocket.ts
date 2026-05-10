// Fixed: Updated WebSocket URL to match backend port and fixed type handling
import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (userId: string) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [presenceUpdates, setPresenceUpdates] = useState<Record<string, boolean>>({});
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(`ws://localhost:8000/ws/${userId}`);

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages(prev => [...prev, data]);
      } else if (data.type === 'presence_update') {
        setPresenceUpdates(prev => ({
          ...prev,
          [data.user_id]: data.is_online
        }));
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [userId]);

  const sendMessage = (message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(message);
    }
  };

  return { messages, presenceUpdates, sendMessage };
};