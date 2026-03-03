import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "../auth-store";
import type { User } from "@/lib/types";

describe("useAuthStore", () => {
  beforeEach(() => {
    window.localStorage.clear();
    // Reset Zustand store to initial state
    useAuthStore.setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isHydrated: false,
    });
  });

  it("initial state has no user, no tokens, isAuthenticated is false", () => {
    const state = useAuthStore.getState();

    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isHydrated).toBe(false);
  });

  it("setTokens sets accessToken, refreshToken, and isAuthenticated to true", () => {
    const { setTokens } = useAuthStore.getState();

    setTokens("access-123", "refresh-456");

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("access-123");
    expect(state.refreshToken).toBe("refresh-456");
    expect(state.isAuthenticated).toBe(true);
  });

  it("setTokens persists tokens to window.localStorage", () => {
    const { setTokens } = useAuthStore.getState();

    setTokens("access-abc", "refresh-def");

    expect(window.localStorage.getItem("access_token")).toBe("access-abc");
    expect(window.localStorage.getItem("refresh_token")).toBe("refresh-def");
  });

  it("setTokens ignores empty access token", () => {
    const { setTokens } = useAuthStore.getState();

    setTokens("", "refresh-456");

    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("setTokens ignores empty refresh token", () => {
    const { setTokens } = useAuthStore.getState();

    setTokens("access-123", "");

    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("setUser sets user without changing tokens", () => {
    const { setTokens, setUser } = useAuthStore.getState();

    setTokens("access-123", "refresh-456");

    const user: User = {
      id: "user-1",
      email: "test@example.com",
      full_name: "Test User",
      is_active: true,
      created_at: "2025-01-01T00:00:00Z",
    };

    setUser(user);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(user);
    expect(state.accessToken).toBe("access-123");
    expect(state.refreshToken).toBe("refresh-456");
    expect(state.isAuthenticated).toBe(true);
  });

  it("logout clears all auth state", () => {
    const { setTokens, setUser, logout } = useAuthStore.getState();

    // Set up authenticated state
    setTokens("access-123", "refresh-456");
    setUser({
      id: "user-1",
      email: "test@example.com",
      full_name: "Test User",
      is_active: true,
      created_at: "2025-01-01T00:00:00Z",
    });

    // Verify authenticated
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    // Logout
    logout();

    const state = useAuthStore.getState();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("logout clears tokens from window.localStorage", () => {
    const { setTokens, logout } = useAuthStore.getState();

    setTokens("access-123", "refresh-456");
    expect(window.localStorage.getItem("access_token")).toBe("access-123");

    logout();

    expect(window.localStorage.getItem("access_token")).toBeNull();
    expect(window.localStorage.getItem("refresh_token")).toBeNull();
  });

  it("isAuthenticated reflects accessToken presence after setTokens", () => {
    const { setTokens } = useAuthStore.getState();

    expect(useAuthStore.getState().isAuthenticated).toBe(false);

    setTokens("token", "refresh");
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });

  it("hydrate reads tokens from window.localStorage and sets isAuthenticated", () => {
    window.localStorage.setItem("access_token", "stored-access");
    window.localStorage.setItem("refresh_token", "stored-refresh");

    const { hydrate } = useAuthStore.getState();
    hydrate();

    const state = useAuthStore.getState();
    expect(state.accessToken).toBe("stored-access");
    expect(state.refreshToken).toBe("stored-refresh");
    expect(state.isAuthenticated).toBe(true);
    expect(state.isHydrated).toBe(true);
  });

  it("hydrate sets isHydrated even when no tokens are stored", () => {
    const { hydrate } = useAuthStore.getState();
    hydrate();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isHydrated).toBe(true);
  });

  it("hydrate does not set isAuthenticated when only access_token is present", () => {
    window.localStorage.setItem("access_token", "stored-access");

    const { hydrate } = useAuthStore.getState();
    hydrate();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isHydrated).toBe(true);
  });
});
