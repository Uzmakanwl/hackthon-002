"use client";

import { useTasks } from "@/hooks/useTasks";
import { TaskCard } from "@/components/TaskCard";

/**
 * Sidebar component displaying the live task list alongside the chat.
 * Auto-refreshes to reflect changes made through the AI assistant.
 */
export function TaskSidebar() {
  const { tasks, isLoading, error } = useTasks();

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-400">
        <p>Loading tasks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center text-red-500">
        <p>Failed to load tasks</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-400">
        <p>No tasks yet. Ask the AI to create one!</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} />
      ))}
    </div>
  );
}
