// Fixed: Added proper WebSocket message type handling
import { useEffect, useRef } from 'react';

interface WebSocketMessage {
  type: 'message' | 'presence';
  message?: any;
  user_id?: string;
  is_online?: boolean;
  last_active?: string;
}

export const useWebSocket = (userId: string, onMessage: (message: WebSocketMessage) => void) => {
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    ws.current = new WebSocket(`ws://localhost:8008/ws/${userId}`);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.current.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);
      onMessage(data);
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [userId, onMessage]);

  const sendMessage = (message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(message);
    }
  };

  return { sendMessage };
};