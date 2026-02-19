// src/types/task.ts

export type TaskStatus = "pending" | "in_progress" | "completed";
export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  tags: string[];
  due_date: string | null;
  reminder_at: string | null;
  is_recurring: boolean;
  recurrence_rule: string | null;
  next_occurrence: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  priority?: TaskPriority;
  tags?: string[];
  due_date?: string;
  reminder_at?: string;
  is_recurring?: boolean;
  recurrence_rule?: string;
}

export interface UpdateTaskInput {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  tags?: string[];
  due_date?: string | null;
  reminder_at?: string | null;
  is_recurring?: boolean;
  recurrence_rule?: string | null;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

export interface TaskFilters {
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
  tag?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
