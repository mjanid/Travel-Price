"use client";

import { create } from "zustand";
import type { User } from "@/lib/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isHydrated: false,

  setTokens: (access, refresh) => {
    if (!access || !refresh) return;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
    }
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
  },

  setUser: (user) => {
    set({ user });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
  },

  hydrate: () => {
    if (typeof window === "undefined") return;
    const access = localStorage.getItem("access_token");
    const refresh = localStorage.getItem("refresh_token");
    if (access && refresh) {
      set({ accessToken: access, refreshToken: refresh, isAuthenticated: true, isHydrated: true });
    } else {
      set({ isHydrated: true });
    }
  },
}));
