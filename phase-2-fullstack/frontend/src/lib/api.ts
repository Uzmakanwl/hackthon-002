// src/lib/api.ts

import type {
  Task,
  CreateTaskInput,
  UpdateTaskInput,
  TaskListResponse,
  TaskFilters,
} from "@/types/task";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function fetchTasks(filters?: TaskFilters): Promise<TaskListResponse> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, value);
    });
  }
  const query = params.toString();
  return fetchAPI<TaskListResponse>(`/api/tasks${query ? `?${query}` : ""}`);
}

export async function fetchTask(id: string): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}`);
}

export async function createTask(data: CreateTaskInput): Promise<Task> {
  return fetchAPI<Task>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTask(id: string, data: UpdateTaskInput): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteTask(id: string): Promise<void> {
  return fetchAPI<void>(`/api/tasks/${id}`, { method: "DELETE" });
}

export async function toggleComplete(id: string): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}/complete`, { method: "POST" });
}
