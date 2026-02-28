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
  fetchMe: () => Promise<void>;
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
      console.log("Login response:", res);
      
      // Save token to localStorage
      tokenHelper.save(res.access_token);
      console.log("Token saved, current token:", tokenHelper.get());
      
      // Fetch full profile so UI always has language/age_group immediately
      const me = await authApi.me();
      set({ user: me, profile: me.profile, isLoading: false });
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
      console.log("Register response:", res);
      
      // Save token to localStorage
      tokenHelper.save(res.access_token);
      console.log("Token saved, current token:", tokenHelper.get());
      
      // Fetch full profile so UI always has language/age_group immediately
      const me = await authApi.me();
      set({ user: me, profile: me.profile, isLoading: false });
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

  fetchMe: async () => {
    set({ isLoading: true });
    try {
      const me = await authApi.me();
      set({ user: me, profile: me.profile, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      if (err.status === 401) {
        set({ user: null, profile: null });
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
