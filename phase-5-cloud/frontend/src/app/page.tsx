"use client";
import { useState, useCallback, useMemo } from "react";
import type { Task, TaskFilters } from "@/types/task";
import { useTasks } from "@/hooks/useTasks";
import { useDebounce } from "@/hooks/useDebounce";
import SearchInput from "@/components/SearchInput";
import FilterBar from "@/components/FilterBar";
import TaskList from "@/components/TaskList";
import TaskForm from "@/components/TaskForm";

export default function Home() {
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<TaskFilters>({
    sort_by: "created_at",
    sort_order: "desc",
  });
  const [toast, setToast] = useState<string | null>(null);

  const debouncedSearch = useDebounce(searchQuery, 300);

  const activeFilters = useMemo(
    () => ({
      ...filters,
      search: debouncedSearch || undefined,
    }),
    [filters, debouncedSearch]
  );

  const { tasks, total, loading, error, refetch } = useTasks(activeFilters);

  const showToast = useCallback((message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  }, []);

  const handleSaved = useCallback(() => {
    refetch();
    showToast(editingTask ? "Task updated!" : "Task created!");
    setEditingTask(null);
  }, [refetch, showToast, editingTask]);

  const handleUpdate = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleEdit = useCallback((task: Task) => {
    setEditingTask(task);
    setShowForm(true);
  }, []);

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  const handleFilterChange = useCallback((newFilters: TaskFilters) => {
    setFilters(newFilters);
  }, []);

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      {/* Toast notification */}
      {toast && (
        <div className="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in">
          {toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Todo App</h1>
          <p className="text-sm text-gray-500 mt-1">{total} task{total !== 1 ? "s" : ""}</p>
        </div>
        <button
          onClick={() => {
            setEditingTask(null);
            setShowForm(true);
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          + Add Task
        </button>
      </div>

      {/* Search and Filters */}
      <div className="space-y-3 mb-6">
        <SearchInput onSearch={handleSearch} />
        <FilterBar filters={filters} onFilterChange={handleFilterChange} />
      </div>

      {/* Task List */}
      <TaskList
        tasks={tasks}
        loading={loading}
        error={error}
        onUpdate={handleUpdate}
        onEdit={handleEdit}
      />

      {/* Task Form Modal */}
      {showForm && (
        <TaskForm
          task={editingTask}
          onClose={() => {
            setShowForm(false);
            setEditingTask(null);
          }}
          onSaved={handleSaved}
        />
      )}
    </main>
  );
}
