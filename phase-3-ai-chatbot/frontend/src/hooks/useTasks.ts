"use client";

import { useState, useEffect, useCallback } from "react";
import type { Task } from "@/types/task";
import { fetchTasks as listTasks } from "@/lib/api";

const POLL_INTERVAL_MS = 5000;

/**
 * Custom hook for fetching and polling the task list.
 *
 * Auto-refreshes on a polling interval so the sidebar reflects
 * changes made through the AI chat in near-real-time.
 */
export function useTasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const response = await listTasks();
      setTasks(response.tasks);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch tasks");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTasks();

    const interval = setInterval(fetchTasks, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  return { tasks, isLoading, error, refetch: fetchTasks };
}
