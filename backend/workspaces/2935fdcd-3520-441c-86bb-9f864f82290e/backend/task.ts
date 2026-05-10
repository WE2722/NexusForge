// TypeScript type definitions for tasks
export type TaskStatus = 'pending' | 'completed';

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
}

export interface TaskCreate {
  title: string;
  description?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
}