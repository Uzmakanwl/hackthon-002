"use client";

import { ChatPanel } from "@/components/ChatPanel";
import { TaskSidebar } from "@/components/TaskSidebar";

export default function HomePage() {
  return (
    <main className="flex h-screen">
      {/* Chat panel — primary interaction area */}
      <section className="flex flex-1 flex-col border-r border-gray-200">
        <header className="border-b border-gray-200 bg-white px-6 py-4">
          <h1 className="text-xl font-semibold">Todo AI Assistant</h1>
          <p className="text-sm text-gray-500">
            Manage your tasks using natural language
          </p>
        </header>
        <ChatPanel />
      </section>

      {/* Task sidebar — live task list for context */}
      <aside className="hidden w-96 flex-col bg-white lg:flex">
        <header className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold">Tasks</h2>
        </header>
        <TaskSidebar />
      </aside>
    </main>
  );
}
