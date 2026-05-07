import React from 'react';
import { TodoList } from './components/TodoList';

const App: React.FC = () => {
  return (
    <div className="max-w-md mx-auto p-4 mt-10">
      <h1 className="text-2xl font-bold mb-4">Todo List App</h1>
      <TodoList />
    </div>
  );
};

export default App;