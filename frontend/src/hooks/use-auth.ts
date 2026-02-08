"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type {
  ApiResponse,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
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
      return res.data!;
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
      return loginRes.data!;
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
      const user = res.data!;
      setUser(user);
      return user;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
    retry: false,
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
