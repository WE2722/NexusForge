// Task creation and update form component
import React, { useState } from 'react';
import { TaskCreate, TaskUpdate } from '../types/task';

interface TaskFormProps {
  onSubmit: (taskData: TaskCreate) => void;
  initialData?: TaskUpdate;
  isEdit?: boolean;
}

export const TaskForm: React.FC<TaskFormProps> = ({
  onSubmit,
  initialData,
  isEdit = false,
}) => {
  const [title, setTitle] = useState<string>(initialData?.title || '');
  const [description, setDescription] = useState<string>(
    initialData?.description || ''
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const taskData: TaskCreate = {
      title: title.trim(),
      ...(description.trim() && { description: description.trim() }),
    };

    onSubmit(taskData);
    setTitle('');
    setDescription('');
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <div className="form-group">
        <label htmlFor="title">Title</label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
      </div>
      <button type="submit" className="submit-button">
        {isEdit ? 'Update Task' : 'Add Task'}
      </button>
    </form>
  );
};