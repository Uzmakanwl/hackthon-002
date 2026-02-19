import type { Task, TaskListResponse, TaskFilters } from "@/types/task";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
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

export async function toggleComplete(id: string): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}/complete`, { method: "POST" });
}

export async function deleteTask(id: string): Promise<void> {
  return fetchAPI<void>(`/api/tasks/${id}`, { method: "DELETE" });
}

export async function sendChatMessage(
  message: string,
  history: Array<{ role: string; content: string }>
): Promise<string> {
  const data = await fetchAPI<{ reply: string }>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
  return data.reply;
}
