// src/store/chatStore.ts
import { create } from "zustand";
import { chatApi, type ChatMessage } from "@/api/client";

interface ChatState {
  sessionId: number | null;
  contextDocumentId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;

  // Actions
  startNewSession: () => void;
  setSessionId: (sessionId: number) => void;
  sendMessage: (payload: {
    question: string;
    documentId?: string;
    contextText?: string;
  }) => Promise<void>;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: null,
  contextDocumentId: null,
  messages: [],
  isLoading: false,
  error: null,

  startNewSession: () => {
    set({
      sessionId: null,
      contextDocumentId: null,
      messages: [],
      error: null,
    });
  },

  setSessionId: (sessionId: number) => {
    set({ sessionId });
  },

  sendMessage: async ({ question, documentId, contextText }) => {
    set({ isLoading: true, error: null });
    try {
      const currentSessionId = get().sessionId;
      const currentContextDocId = get().contextDocumentId;
      const response = await chatApi.chat({
        document_id: documentId || currentContextDocId || undefined,
        context_text: contextText,
        user_question: question,
        session_id: currentSessionId,
      });

      // Add user message
      const userMsg: ChatMessage = {
        message_id: response.message_id - 1,
        role: "user",
        content: question,
        referenced_paragraphs: [],
        confidence: null,
        out_of_scope: false,
        processing_ms: null,
        created_at: new Date().toISOString(),
      };

      // Add assistant message
      const assistantMsg: ChatMessage = {
        message_id: response.message_id,
        role: "assistant",
        content: response.answer,
        referenced_paragraphs: response.referenced_paragraphs,
        confidence: response.confidence,
        out_of_scope: response.out_of_scope,
        processing_ms: response.processing_ms,
        created_at: response.created_at,
      };

      set((state) => ({
        sessionId: response.session_id,
        contextDocumentId: response.document_id,
        messages: [...state.messages, userMsg, assistantMsg],
        isLoading: false,
      }));
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));
