"use client";

import { useChat } from "@/hooks/useChat";
import { ChatMessageBubble } from "@/components/ChatMessage";
import { ChatInput } from "@/components/ChatInput";

/**
 * Main chat panel component displaying conversation history and input.
 * Handles the conversational UI for AI-powered task management.
 */
export function ChatPanel() {
  const { messages, isLoading, sendMessage } = useChat();

  return (
    <div className="flex flex-1 flex-col">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-gray-400">
            <p>Start a conversation to manage your tasks with AI.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <ChatMessageBubble key={index} message={message} />
        ))}
      </div>

      {/* Input area */}
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}
