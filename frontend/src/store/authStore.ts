// src/store/authStore.ts
import { create } from "zustand";
import { authApi, tokenHelper, type User, type UserWithProfile } from "@/api/client";

interface AuthState {
  user: User | null;
  profile: UserWithProfile["profile"] | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  register: (data: { username: string; password: string; nickname: string; age_group?: string }) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: (options?: { background?: boolean }) => Promise<void>;
  updateProfile: (data: { role?: string; age_group?: string }) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  profile: null,
  isLoading: false,
  error: null,

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login(username, password);
      tokenHelper.save(res.access_token);
      // Do not block login UX on an extra /auth/me round-trip.
      set({ user: res.user, profile: null, isLoading: false });
    } catch (err: any) {
      console.error("Login error:", err);
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.register(data);
      tokenHelper.save(res.access_token);
      // Do not block register UX on an extra /auth/me round-trip.
      set({ user: res.user, profile: null, isLoading: false });
    } catch (err: any) {
      console.error("Register error:", err);
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  logout: async () => {
    set({ isLoading: true, error: null });
    try {
      // Call backend logout endpoint to clear cookies
      await tokenHelper.clear();
      set({ user: null, profile: null, error: null, isLoading: false });
    } catch (err: any) {
      // Still clear local state even if logout call fails
      set({ user: null, profile: null, error: null, isLoading: false });
    }
  },

  fetchMe: async (options) => {
    const background = options?.background ?? false;
    if (!background) {
      set({ isLoading: true });
    }

    try {
      const me = await authApi.me();
      if (background) {
        set({ user: me, profile: me.profile, error: null });
      } else {
        set({ user: me, profile: me.profile, error: null, isLoading: false });
      }
    } catch (err: any) {
      if (err.status === 401) {
        // Silent failure for expired/invalid session during app bootstrap.
        if (background) {
          set({ user: null, profile: null, error: null });
        } else {
          set({ user: null, profile: null, error: null, isLoading: false });
        }
        return;
      }
      if (background) {
        set({ error: null });
      } else {
        set({ error: err.message, isLoading: false });
      }
    }
  },

  updateProfile: async (data: any) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await authApi.updateProfile(data);
      set((state) => ({
        profile: updated,
        user: state.user ? { ...state.user, language: updated.language } : null,
        isLoading: false,
      }));
    } catch (err: any) {
      if (err?.status === 401) {
        set({ user: null, profile: null, error: err.message, isLoading: false });
      } else {
        set({ error: err.message, isLoading: false });
      }
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));
