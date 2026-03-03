"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type {
  ApiResponse,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UpdateProfileRequest,
  User,
} from "@/lib/types";
import { useAuthStore } from "@/stores/auth-store";
import {
  apiResponseSchema,
  tokenResponseSchema,
  userResponseSchema,
} from "@/lib/validators";

const tokenEnvelope = apiResponseSchema(tokenResponseSchema);
const userEnvelope = apiResponseSchema(userResponseSchema);

export function useLogin() {
  const { setTokens } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const raw = await api.post<ApiResponse<TokenResponse>>(
        "/api/v1/auth/login",
        data,
      );
      const res = tokenEnvelope.parse(raw);
      if (!res.data) throw new Error("Invalid login response");
      return res.data;
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      router.push("/dashboard");
    },
  });
}

export function useRegister() {
  const { setTokens } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      await api.post<ApiResponse<User>>("/api/v1/auth/register", data);
      const raw = await api.post<ApiResponse<TokenResponse>>(
        "/api/v1/auth/login",
        { email: data.email, password: data.password },
      );
      const res = tokenEnvelope.parse(raw);
      if (!res.data) throw new Error("Invalid login response");
      return res.data;
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      router.push("/dashboard");
    },
  });
}

export function useCurrentUser() {
  const { isAuthenticated, setUser } = useAuthStore();

  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const raw = await api.get<ApiResponse<User>>("/api/v1/auth/me");
      const res = userEnvelope.parse(raw);
      if (!res.data) throw new Error("Invalid user response");
      setUser(res.data as User);
      return res.data as User;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UpdateProfileRequest) => {
      const raw = await api.patch<ApiResponse<User>>(
        "/api/v1/auth/me",
        data,
      );
      const res = userEnvelope.parse(raw);
      if (!res.data) throw new Error("Invalid profile response");
      return res.data as User;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
    },
  });
}

export function useLogout() {
  const { logout } = useAuthStore();
  const queryClient = useQueryClient();
  const router = useRouter();

  return async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } catch {
      // Best-effort: clear local state even if server call fails
    }
    logout();
    queryClient.clear();
    router.push("/login");
  };
}
