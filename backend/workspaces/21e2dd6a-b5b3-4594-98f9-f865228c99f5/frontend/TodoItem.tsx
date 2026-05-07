import React from 'react';
import { FaCheck, FaTrash } from 'react-icons/fa';

interface TodoItemProps {
  todo: { id: number; text: string; completed: boolean };
  onDeleteTask: (id: number) => void;
  onToggleCompleted: (id: number) => void;
}

const TodoItem: React.FC<TodoItemProps> = ({ todo, onDeleteTask, onToggleCompleted }) => {
  return (
    <li className="mb-2">
      <span
        className={`text-lg font-bold ${todo.completed ? 'line-through' : ''}`}
        onClick={() => onToggleCompleted(todo.id)}
      >
        {todo.text}
      </span>
      <button
        className="ml-2 text-lg text-red-500 hover:text-red-700"
        onClick={() => onDeleteTask(todo.id)}
      >
        <FaTrash />
      </button>
    </li>
  );
};

export default TodoItem;