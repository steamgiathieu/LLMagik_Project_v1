// src/store/documentStore.ts
import { create } from "zustand";
import { textsApi, type Document, type DocumentSummary } from "@/api/client";

interface DocumentState {
  documents: DocumentSummary[];
  currentDocument: Document | null;
  selectedParagraphId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchDocuments: () => Promise<void>;
  fetchDocument: (docId: string) => Promise<void>;
  deleteDocument: (docId: string) => Promise<void>;
  setSelectedParagraph: (paragraphId: string | null) => void;
  clearError: () => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  currentDocument: null,
  selectedParagraphId: null,
  isLoading: false,
  error: null,

  fetchDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      const docs = await textsApi.list();
      set({ documents: docs, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  fetchDocument: async (docId: string) => {
    set({ isLoading: true, error: null });
    try {
      const doc = await textsApi.get(docId);
      set({ currentDocument: doc, selectedParagraphId: null, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  deleteDocument: async (docId: string) => {
    set({ error: null });
    try {
      await textsApi.delete(docId);
      set((state) => ({
        documents: state.documents.filter((d) => d.document_id !== docId),
      }));
    } catch (err: any) {
      set({ error: err.message });
      throw err;
    }
  },

  setSelectedParagraph: (paragraphId: string | null) => {
    set({ selectedParagraphId: paragraphId });
  },

  clearError: () => {
    set({ error: null });
  },
}));
