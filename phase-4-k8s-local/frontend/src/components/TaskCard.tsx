"use client";
import type { Task } from "@/types/task";
import { toggleComplete, deleteTask } from "@/lib/api";

interface TaskCardProps {
  task: Task;
  onUpdate: () => void;
  onEdit: (task: Task) => void;
}

const priorityColors: Record<string, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

const statusIcons: Record<string, string> = {
  pending: "\u25CB",
  in_progress: "\u25D1",
  completed: "\u25CF",
};

export default function TaskCard({ task, onUpdate, onEdit }: TaskCardProps) {
  const handleToggle = async () => {
    try {
      await toggleComplete(task.id);
      onUpdate();
    } catch (err) {
      console.error("Failed to toggle:", err);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteTask(task.id);
      onUpdate();
    } catch (err) {
      console.error("Failed to delete:", err);
    }
  };

  const isOverdue =
    task.due_date &&
    task.status !== "completed" &&
    new Date(task.due_date) < new Date();

  return (
    <div
      className={`p-4 border rounded-lg shadow-sm hover:shadow-md transition-shadow ${
        task.status === "completed" ? "bg-gray-50 opacity-75" : "bg-white"
      } ${isOverdue ? "border-red-300" : "border-gray-200"}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <button
            onClick={handleToggle}
            className="mt-0.5 text-xl hover:scale-110 transition-transform flex-shrink-0"
            title={task.status === "completed" ? "Mark pending" : "Mark complete"}
          >
            {statusIcons[task.status] || "\u25CB"}
          </button>
          <div className="flex-1 min-w-0">
            <h3
              className={`font-medium truncate ${
                task.status === "completed" ? "line-through text-gray-500" : "text-gray-900"
              }`}
            >
              {task.title}
            </h3>
            {task.description && (
              <p className="text-sm text-gray-500 mt-1 line-clamp-2">{task.description}</p>
            )}
            <div className="flex flex-wrap items-center gap-2 mt-2">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priorityColors[task.priority]}`}>
                {task.priority}
              </span>
              {task.tags.map((tag) => (
                <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                  {tag}
                </span>
              ))}
              {task.due_date && (
                <span className={`text-xs ${isOverdue ? "text-red-600 font-medium" : "text-gray-500"}`}>
                  Due: {new Date(task.due_date).toLocaleDateString()}
                </span>
              )}
              {task.is_recurring && (
                <span className="text-xs text-purple-600">{"\u21BB"} {task.recurrence_rule}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-1 flex-shrink-0">
          <button
            onClick={() => onEdit(task)}
            className="p-1.5 text-gray-400 hover:text-blue-600 rounded hover:bg-blue-50 transition-colors"
            title="Edit"
          >
            {"\u270E"}
          </button>
          <button
            onClick={handleDelete}
            className="p-1.5 text-gray-400 hover:text-red-600 rounded hover:bg-red-50 transition-colors"
            title="Delete"
          >
            {"\u2715"}
          </button>
        </div>
      </div>
    </div>
  );
}
