import React, { useState, useEffect } from 'react';
import { TodoItem } from './TodoItem';
import { AddTask } from './AddTask';
import axios from 'axios';

interface Todo {
  id: number;
  text: string;
  completed: boolean;
}

interface TodoListProps {}

const TodoList: React.FC<TodoListProps> = () => {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTodos = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/todos');
        setTodos(response.data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };
    fetchTodos();
  }, []);

  const handleAddTask = async (text: string) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/todos', { text });
      setTodos((prevTodos) => [...prevTodos, response.data]);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTask = async (id: number) => {
    setLoading(true);
    try {
      await axios.delete(`/api/todos/${id}`);
      setTodos((prevTodos) => prevTodos.filter((todo) => todo.id !== id));
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCompleted = async (id: number) => {
    setLoading(true);
    try {
      const response = await axios.patch(`/api/todos/${id}`, { completed: !todos.find((todo) => todo.id === id)?.completed });
      setTodos((prevTodos) => prevTodos.map((todo) => (todo.id === id ? { ...todo, completed: response.data.completed } : todo)));
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          {error ? (
            <p style={{ color: 'red' }}>{error}</p>
          ) : (
            <div>
              <AddTask onAddTask={handleAddTask} />
              <ul>
                {todos.map((todo) => (
                  <TodoItem
                    key={todo.id}
                    todo={todo}
                    onDeleteTask={handleDeleteTask}
                    onToggleCompleted={handleToggleCompleted}
                  />
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TodoList;