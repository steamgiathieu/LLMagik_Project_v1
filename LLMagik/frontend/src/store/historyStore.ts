// src/store/historyStore.ts
import { create } from "zustand";
import { historyApi } from "@/api/client";

export interface HistoryEntry {
  history_id: number;
  activity_type: "analysis" | "rewrite" | "chat";
  document_id: string;
  document_title: string | null;
  timestamp: string;
  data: Record<string, any>;
}

interface HistoryState {
  entries: HistoryEntry[];
  isLoading: boolean;
  error: string | null;
  filter: "all" | "analysis" | "rewrite" | "chat";

  // Actions
  fetchHistory: () => Promise<void>;
  setFilter: (filter: "all" | "analysis" | "rewrite" | "chat") => void;
  clearError: () => void;
}

export const useHistoryStore = create<HistoryState>((set) => ({
  entries: [],
  isLoading: false,
  error: null,
  filter: "all",

  fetchHistory: async () => {
    set({ isLoading: true, error: null });
    try {
      // Note: This is a simplified mock since the backend history API needs more details
      // In real implementation, you'd need to fetch from multiple endpoints
      const analysisHistory = (await historyApi.analyses()) as any[];
      
      // Convert to unified format
      const entries: HistoryEntry[] = analysisHistory.map((item: any) => ({
        history_id: item.analysis_id,
        activity_type: "analysis" as const,
        document_id: item.document_id,
        document_title: null,
        timestamp: item.created_at,
        data: item,
      }));

      set({ entries, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  setFilter: (filter: "all" | "analysis" | "rewrite" | "chat") => {
    set({ filter });
  },

  clearError: () => {
    set({ error: null });
  },
}));
