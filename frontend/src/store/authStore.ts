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
  register: (data: { username: string; email: string; password: string; nickname: string }) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  updateProfile: (data: { language?: string; role?: string; age_group?: string }) => Promise<void>;
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
      set({ user: res.user, isLoading: false });
      // Fetch full profile after login
      const me = await authApi.me();
      set({ profile: me.profile });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.register(data);
      tokenHelper.save(res.access_token);
      set({ user: res.user, isLoading: false });
      // Fetch profile
      const me = await authApi.me();
      set({ profile: me.profile });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    tokenHelper.clear();
    set({ user: null, profile: null, error: null });
  },

  fetchMe: async () => {
    if (!tokenHelper.exists()) return;
    set({ isLoading: true });
    try {
      const me = await authApi.me();
      set({ user: me, profile: me.profile, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      if (err.status === 401) {
        tokenHelper.clear();
        set({ user: null, profile: null });
      }
    }
  },

  updateProfile: async (data: any) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await authApi.updateProfile(data);
      set({ profile: updated, isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));
