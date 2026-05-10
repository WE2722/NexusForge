// Fixed: Updated API endpoints to match backend structure
const API_BASE_URL = 'http://localhost:8008/api/v1';

export const createUser = async (username: string) => {
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username })
  });
  if (!response.ok) throw new Error('Failed to create user');
  return response.json();
};

export const getUser = async (userId: string) => {
  const response = await fetch(`${API_BASE_URL}/users/${userId}`);
  if (!response.ok) throw new Error('Failed to fetch user');
  return response.json();
};

export const createRoom = async (name: string, creatorId: string) => {
  const response = await fetch(`${API_BASE_URL}/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, creator_id: creatorId })
  });
  if (!response.ok) throw new Error('Failed to create room');
  return response.json();
};

export const listRooms = async () => {
  const response = await fetch(`${API_BASE_URL}/rooms`);
  if (!response.ok) throw new Error('Failed to fetch rooms');
  return response.json();
};

export const getRoom = async (roomId: string) => {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`);
  if (!response.ok) throw new Error('Failed to fetch room');
  return response.json();
};

export const joinRoom = async (roomId: string, userId: string) => {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId })
  });
  if (!response.ok) throw new Error('Failed to join room');
  return response.json();
};

export const sendMessage = async (roomId: string, userId: string, content: string) => {
  const response = await fetch(`${API_BASE_URL}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room_id: roomId, user_id: userId, content })
  });
  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
};

export const getRoomMessages = async (roomId: string) => {
  const response = await fetch(`${API_BASE_URL}/rooms/${roomId}/messages`);
  if (!response.ok) throw new Error('Failed to fetch messages');
  return response.json();
};