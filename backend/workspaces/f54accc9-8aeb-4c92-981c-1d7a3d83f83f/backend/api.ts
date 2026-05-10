// TypeScript API types
export interface User {
  id: string;
  username: string;
  isOnline: boolean;
  lastActive: string;
}

export interface ChatRoom {
  id: string;
  name: string;
  createdAt: string;
  participants: string[];
}

export interface Message {
  id: string;
  roomId: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: string;
  isRead: boolean;
}

export interface CreateRoomRequest {
  name: string;
  participantIds: string[];
}

export interface SendMessageRequest {
  content: string;
}

export interface RoomWithParticipants {
  room: ChatRoom;
  participants: User[];
}

export interface UserPresenceUpdate {
  userId: string;
  isOnline: boolean;
}