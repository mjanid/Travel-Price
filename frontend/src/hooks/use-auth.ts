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

export function useLogin() {
  const { setTokens } = useAuthStore();
  const router = useRouter();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const res = await api.post<ApiResponse<TokenResponse>>(
        "/api/v1/auth/login",
        data,
      );
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
      const loginRes = await api.post<ApiResponse<TokenResponse>>(
        "/api/v1/auth/login",
        { email: data.email, password: data.password },
      );
      if (!loginRes.data) throw new Error("Invalid login response");
      return loginRes.data;
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
      const res = await api.get<ApiResponse<User>>("/api/v1/auth/me");
      if (!res.data) throw new Error("Invalid user response");
      setUser(res.data);
      return res.data;
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
      const res = await api.patch<ApiResponse<User>>(
        "/api/v1/auth/me",
        data,
      );
      if (!res.data) throw new Error("Invalid profile response");
      return res.data;
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

  return () => {
    logout();
    queryClient.clear();
    router.push("/login");
  };
}
