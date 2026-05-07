import React, { useState, useEffect } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import TodoList from './components/TodoList';
import CreateTaskForm from './components/CreateTaskForm';

interface ITodo {
  id: number;
  title: string;
  completed: boolean;
}

interface ITodoListProps {
  todos: ITodo[];
  onDelete: (id: number) => void;
  onToggle: (id: number) => void;
}

const App: React.FC = () => {
  const [todos, setTodos] = useState<ITodo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchTodos = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/todos');
        const data = await response.json();
        setTodos(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchTodos();
  }, []);

  const handleDelete = (id: number) => {
    setTodos(todos.filter((todo) => todo.id !== id));
  };

  const handleToggle = (id: number) => {
    setTodos(
      todos.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };

  return (
    <BrowserRouter>
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-4">Todo List App</h1>
        <CreateTaskForm />
        {loading ? (
          <p className="text-lg font-bold">Loading...</p>
        ) : (
          <TodoList
            todos={todos}
            onDelete={handleDelete}
            onToggle={handleToggle}
          />
        )}
      </div>
    </BrowserRouter>
  );
};

export default App;