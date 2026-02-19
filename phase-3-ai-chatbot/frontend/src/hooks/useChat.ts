"use client";

import { useState, useCallback } from "react";
import type { ChatMessage } from "@/types/chat";
import { sendChatMessage } from "@/lib/api";

/**
 * Custom hook for managing chat state and communication with the AI agent.
 *
 * Tracks conversation history, loading state, and provides a sendMessage
 * function that appends user/assistant messages to the history.
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const history = messages.map((m) => ({ role: m.role, content: m.content }));
        const response = await sendChatMessage(content, history);

        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: response,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        const errorMessage: ChatMessage = {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages]
  );

  return { messages, isLoading, sendMessage };
}
