"use client";

import type { Task } from "@/types/task";

interface TaskCardProps {
  task: Task;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

/**
 * Compact task card for display in the sidebar.
 * Shows title, status, priority badge, and due date.
 */
export function TaskCard({ task }: TaskCardProps) {
  const isCompleted = task.status === "completed";
  const isOverdue =
    task.due_date && !isCompleted && new Date(task.due_date) < new Date();

  return (
    <div
      className={`rounded-lg border p-3 ${
        isCompleted ? "border-gray-200 bg-gray-50 opacity-60" : "border-gray-200 bg-white"
      } ${isOverdue ? "border-red-300" : ""}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3
          className={`text-sm font-medium ${
            isCompleted ? "line-through text-gray-400" : ""
          }`}
        >
          {task.title}
        </h3>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
            PRIORITY_COLORS[task.priority] || ""
          }`}
        >
          {task.priority}
        </span>
      </div>

      {task.due_date && (
        <p className={`mt-1 text-xs ${isOverdue ? "text-red-600 font-medium" : "text-gray-500"}`}>
          Due: {new Date(task.due_date).toLocaleDateString()}
          {isOverdue && " (overdue)"}
        </p>
      )}

      {task.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {task.tags.map((tag) => (
            <span
              key={tag}
              className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {task.is_recurring && task.recurrence_rule && (
        <p className="mt-1 text-xs text-blue-500">
          Repeats {task.recurrence_rule}
        </p>
      )}
    </div>
  );
}
