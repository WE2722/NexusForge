import React from 'react';
import { ITodo } from '../App';

export interface ITodoListProps {
  todos: ITodo[];
  onDelete: (id: number) => void;
  onToggle: (id: number) => void;
}

const TodoList: React.FC<ITodoListProps> = ({ todos, onDelete, onToggle }) => {
  return (
    <ul className="list-disc list-inside">
      {todos.map((todo) => (
        <li key={todo.id}>
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={() => onToggle(todo.id)}
            className="mr-2"
          />
          <span
            className={`text-lg font-bold ${
              todo.completed ? 'line-through' : ''
            }`}
          >
            {todo.title}
          </span>
          <button
            className="ml-4 text-lg font-bold"
            onClick={() => onDelete(todo.id)}
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
};

export default TodoList;