// src/hooks/useTasks.ts
"use client";
import { useState, useEffect, useCallback } from "react";
import type { Task, TaskFilters, TaskListResponse } from "@/types/task";
import { fetchTasks } from "@/lib/api";

export function useTasks(filters?: TaskFilters) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: TaskListResponse = await fetchTasks(filters);
      setTasks(data.tasks);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  return { tasks, total, loading, error, refetch: loadTasks };
}
