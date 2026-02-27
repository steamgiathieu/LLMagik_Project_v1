// src/store/analysisStore.ts
import { create } from "zustand";
import { analysisApi, type AnalysisResult, type Paragraph } from "@/api/client";

interface AnalysisState {
  currentResult: AnalysisResult | null;
  mode: "reader" | "writer";
  isAnalyzing: boolean;
  error: string | null;
  history: AnalysisResult[];

  // Actions
  analyze: (docId: string, mode: "reader" | "writer", paragraphs: Paragraph[]) => Promise<void>;
  setMode: (mode: "reader" | "writer") => void;
  fetchHistory: () => Promise<void>;
  clearError: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentResult: null,
  mode: "reader",
  isAnalyzing: false,
  error: null,
  history: [],

  analyze: async (docId: string, mode: "reader" | "writer", paragraphs: Paragraph[]) => {
    set({ isAnalyzing: true, error: null, currentResult: null });
    try {
      const result = await analysisApi.analyze({
        document_id: docId,
        mode: mode,
        paragraphs: paragraphs.map((p) => ({ id: p.id, text: p.text })),
      });
      set({ currentResult: result, isAnalyzing: false });
    } catch (err: any) {
      set({ error: err.message, isAnalyzing: false });
      throw err;
    }
  },

  setMode: (mode: "reader" | "writer") => {
    set({ mode });
  },

  fetchHistory: async () => {
    try {
      const results = await analysisApi.history();
      set({ history: results });
    } catch (err: any) {
      set({ error: err.message });
      throw err;
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));
