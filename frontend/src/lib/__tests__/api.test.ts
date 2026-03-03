import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { ApiResponse, TokenResponse } from "../types";

// ----------------------------------------------------------------
// We need a clean module state for every test because the module-level
// `refreshPromise` variable is shared. We also mock `fetch` globally.
// ----------------------------------------------------------------

const API_URL = "http://localhost:8000";

// Helper: create a minimal Response-like object for fetch mock
function jsonResponse(
  body: unknown,
  status = 200,
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    headers: new Headers(),
    redirected: false,
    statusText: "OK",
    type: "basic" as ResponseType,
    url: "",
    clone: () => jsonResponse(body, status) as Response,
    body: null,
    bodyUsed: false,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    text: () => Promise.resolve(JSON.stringify(body)),
    bytes: () => Promise.resolve(new Uint8Array()),
  } as Response;
}

describe("API client", () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Clear localStorage before each test
    // Use window.localStorage (jsdom) because Node.js 25's built-in
    // localStorage lacks the .clear() method.
    window.localStorage.clear();

    // Set up fetch spy
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  async function loadApi() {
    const mod = await import("../api");
    return mod;
  }

  it("attaches Authorization header when token exists in localStorage", async () => {
    window.localStorage.setItem("access_token", "my-access-token");

    fetchSpy.mockResolvedValueOnce(
      jsonResponse({ data: { id: "1" }, meta: {} }),
    );

    const { api } = await loadApi();
    await api.get("/api/v1/test");

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, options] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${API_URL}/api/v1/test`);
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer my-access-token");
  });

  it("makes request without Authorization header when no token", async () => {
    fetchSpy.mockResolvedValueOnce(
      jsonResponse({ data: null, meta: {} }),
    );

    const { api } = await loadApi();
    await api.get("/api/v1/public");

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [, options] = fetchSpy.mock.calls[0] as [string, RequestInit];
    const headers = options.headers as Record<string, string>;
    expect(headers["Authorization"]).toBeUndefined();
  });

  it("refreshes token on 401 response and retries original request", async () => {
    window.localStorage.setItem("access_token", "expired-token");
    window.localStorage.setItem("refresh_token", "valid-refresh");

    const refreshResponse: ApiResponse<TokenResponse> = {
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
        token_type: "bearer",
      },
    };

    // First call: 401
    fetchSpy.mockResolvedValueOnce(jsonResponse({ errors: ["Unauthorized"] }, 401));
    // Refresh call: success
    fetchSpy.mockResolvedValueOnce(jsonResponse(refreshResponse));
    // Retry: success
    fetchSpy.mockResolvedValueOnce(jsonResponse({ data: { id: "1" } }));

    const { api } = await loadApi();
    const result = await api.get<{ data: { id: string } }>("/api/v1/protected");

    expect(fetchSpy).toHaveBeenCalledTimes(3);

    // Verify the refresh call
    const [refreshUrl, refreshOptions] = fetchSpy.mock.calls[1] as [string, RequestInit];
    expect(refreshUrl).toBe(`${API_URL}/api/v1/auth/refresh`);
    expect(refreshOptions.method).toBe("POST");
    const refreshBody = JSON.parse(refreshOptions.body as string) as { refresh_token: string };
    expect(refreshBody.refresh_token).toBe("valid-refresh");

    // Verify retry uses new token
    const [, retryOptions] = fetchSpy.mock.calls[2] as [string, RequestInit];
    const retryHeaders = retryOptions.headers as Record<string, string>;
    expect(retryHeaders["Authorization"]).toBe("Bearer new-access-token");

    // Verify localStorage was updated
    expect(window.localStorage.getItem("access_token")).toBe("new-access-token");
    expect(window.localStorage.getItem("refresh_token")).toBe("new-refresh-token");

    expect(result).toEqual({ data: { id: "1" } });
  });

  it("logs out when refresh also returns 401", async () => {
    window.localStorage.setItem("access_token", "expired-token");
    window.localStorage.setItem("refresh_token", "expired-refresh");

    // Original request: 401
    fetchSpy.mockResolvedValueOnce(jsonResponse({ errors: ["Unauthorized"] }, 401));
    // Refresh: fails (non-ok)
    fetchSpy.mockResolvedValueOnce(jsonResponse({ errors: ["Invalid refresh"] }, 401));

    const { api } = await loadApi();

    await expect(api.get("/api/v1/protected")).rejects.toThrow("Session expired");

    // Tokens should be cleared from localStorage
    expect(window.localStorage.getItem("access_token")).toBeNull();
    expect(window.localStorage.getItem("refresh_token")).toBeNull();
  });

  it("does not retry non-401 errors (e.g., 403, 500)", async () => {
    window.localStorage.setItem("access_token", "valid-token");

    // 403 response
    fetchSpy.mockResolvedValueOnce(
      jsonResponse({ errors: ["Forbidden"] }, 403),
    );

    const { api } = await loadApi();

    await expect(api.get("/api/v1/admin-only")).rejects.toThrow("Forbidden");

    // Only one fetch call - no refresh attempted
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("does not retry 500 errors", async () => {
    window.localStorage.setItem("access_token", "valid-token");

    fetchSpy.mockResolvedValueOnce(
      jsonResponse({ detail: "Internal Server Error" }, 500),
    );

    const { api } = await loadApi();

    await expect(api.get("/api/v1/broken")).rejects.toThrow("Internal Server Error");

    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("queues concurrent requests during token refresh — no duplicate refresh calls", async () => {
    window.localStorage.setItem("access_token", "expired-token");
    window.localStorage.setItem("refresh_token", "valid-refresh");

    const refreshResponse: ApiResponse<TokenResponse> = {
      data: {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
        token_type: "bearer",
      },
    };

    // We need to carefully orchestrate the mock:
    // Call 1: first request -> 401
    // Call 2: second request -> 401
    // Call 3: refresh -> success (only ONE refresh should happen)
    // Call 4: retry first request -> success
    // Call 5: retry second request -> success
    fetchSpy
      .mockResolvedValueOnce(jsonResponse({ errors: ["Unauthorized"] }, 401))
      .mockResolvedValueOnce(jsonResponse({ errors: ["Unauthorized"] }, 401))
      .mockResolvedValueOnce(jsonResponse(refreshResponse))
      .mockResolvedValueOnce(jsonResponse({ data: { id: "1" } }))
      .mockResolvedValueOnce(jsonResponse({ data: { id: "2" } }));

    const { api } = await loadApi();

    // Fire two requests concurrently
    const [result1, result2] = await Promise.all([
      api.get<{ data: { id: string } }>("/api/v1/resource/1"),
      api.get<{ data: { id: string } }>("/api/v1/resource/2"),
    ]);

    // Verify results
    expect(result1).toEqual({ data: { id: "1" } });
    expect(result2).toEqual({ data: { id: "2" } });

    // Count refresh calls: should be exactly 1
    const refreshCalls = fetchSpy.mock.calls.filter(
      (call: unknown[]) => (call[0] as string).includes("/auth/refresh"),
    );
    expect(refreshCalls).toHaveLength(1);
  });

  it("sends POST body as JSON", async () => {
    fetchSpy.mockResolvedValueOnce(
      jsonResponse({ data: { id: "new" } }),
    );

    const { api } = await loadApi();
    await api.post("/api/v1/items", { name: "test" });

    const [, options] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body as string)).toEqual({ name: "test" });
    const headers = options.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("handles 204 No Content response", async () => {
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 204,
      headers: new Headers(),
      redirected: false,
      statusText: "No Content",
      type: "basic" as ResponseType,
      url: "",
      clone: vi.fn(),
      body: null,
      bodyUsed: false,
      json: () => Promise.reject(new Error("no body")),
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
      blob: () => Promise.resolve(new Blob()),
      formData: () => Promise.resolve(new FormData()),
      text: () => Promise.resolve(""),
      bytes: () => Promise.resolve(new Uint8Array()),
    } as Response);

    const { api } = await loadApi();
    const result = await api.delete("/api/v1/items/1");

    expect(result).toBeUndefined();
  });
});
