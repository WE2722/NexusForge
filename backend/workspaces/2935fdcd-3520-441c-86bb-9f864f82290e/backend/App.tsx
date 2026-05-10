// Fixed: Updated API endpoints from port 8008 to 8000 to match backend
import React, { useState, useEffect } from 'react';
import './App.css';

export interface Task {
  id: number;
  title: string;
  description?: string;
  status: 'pending' | 'completed';
}

export interface TaskCreate {
  title: string;
  description?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: 'pending' | 'completed';
}

const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTask, setNewTask] = useState<TaskCreate>({ title: '', description: '' });
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState<boolean>(false);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/tasks/');
      if (!response.ok) throw new Error('Failed to fetch tasks');
      const data = await response.json();
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const createTask = async () => {
    if (!newTask.title.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/tasks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTask),
      });
      if (!response.ok) throw new Error('Failed to create task');
      const createdTask = await response.json();
      setTasks(prev => [...prev, createdTask]);
      setNewTask({ title: '', description: '' });
      setIsAdding(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const updateTask = async (taskId: number, updates: TaskUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error('Failed to update task');
      const updatedTask = await response.json();
      setTasks(prev => prev.map(task =>
        task.id === taskId ? updatedTask : task
      ));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const deleteTask = async (taskId: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/tasks/${taskId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete task');
      setTasks(prev => prev.filter(task => task.id !== taskId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    return task.status === filter;
  });

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Todo Application</h1>
        <p>Manage your tasks efficiently</p>
      </header>

      <div className="controls">
        <div className="filter-buttons">
          <button
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={filter === 'pending' ? 'active' : ''}
            onClick={() => setFilter('pending')}
          >
            Pending
          </button>
          <button
            className={filter === 'completed' ? 'active' : ''}
            onClick={() => setFilter('completed')}
          >
            Completed
          </button>
        </div>

        <button
          className="add-button"
          onClick={() => setIsAdding(!isAdding)}
        >
          {isAdding ? 'Cancel' : 'Add New Task'}
        </button>
      </div>

      {isAdding && (
        <div className="task-form-container">
          <div className="task-form">
            <input
              type="text"
              placeholder="Task title"
              value={newTask.title}
              onChange={(e) => setNewTask({...newTask, title: e.target.value})}
              className="task-input"
            />
            <textarea
              placeholder="Description (optional)"
              value={newTask.description}
              onChange={(e) => setNewTask({...newTask, description: e.target.value})}
              className="task-textarea"
              rows={3}
            />
            <button
              onClick={createTask}
              className="submit-button"
              disabled={!newTask.title.trim()}
            >
              Add Task
            </button>
          </div>
        </div>
      )}

      {loading && <div className="loading">Loading tasks...</div>}

      {error && <div className="error-message">{error}</div>}

      <div className="tasks-container">
        {filteredTasks.length === 0 ? (
          <div className="empty-state">
            {filter === 'all' ? 'No tasks yet. Add one!' : `No ${filter} tasks found.`}
          </div>
        ) : (
          filteredTasks.map(task => (
            <div
              key={task.id}
              className={`task-card ${task.status}`}
              style={{ animationDelay: `${task.id * 0.1}s` }}
            >
              <div className="task-header">
                <h3>{task.title}</h3>
                <div className="task-actions">
                  <button
                    className="action-button complete"
                    onClick={() => updateTask(task.id, { status: task.status === 'pending' ? 'completed' : 'pending' })}
                    title={task.status === 'pending' ? 'Mark as completed' : 'Mark as pending'}
                  >
                    {task.status === 'pending' ? '✓' : '↻'}
                  </button>
                  <button
                    className="action-button delete"
                    onClick={() => deleteTask(task.id)}
                    title="Delete task"
                  >
                    ×
                  </button>
                </div>
              </div>
              {task.description && (
                <p className="task-description">{task.description}</p>
              )}
              <div className="task-status">
                Status: <span className={task.status}>{task.status}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default App;