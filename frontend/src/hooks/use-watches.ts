"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import type {
  ApiResponse,
  PaginatedResponse,
  PriceWatch,
  PriceWatchCreateRequest,
  PriceWatchUpdateRequest,
} from "@/lib/types";

export function useWatches(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["watches", page, perPage],
    queryFn: () =>
      api.get<PaginatedResponse<PriceWatch>>(
        `/api/v1/watches/?page=${page}&per_page=${perPage}`,
      ),
  });
}

export function useWatch(id: string) {
  return useQuery({
    queryKey: ["watch", id],
    queryFn: () => api.get<ApiResponse<PriceWatch>>(`/api/v1/watches/${id}`),
    enabled: !!id,
  });
}

export function useTripWatches(tripId: string, page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["tripWatches", tripId, page, perPage],
    queryFn: () =>
      api.get<PaginatedResponse<PriceWatch>>(
        `/api/v1/trips/${tripId}/watches?page=${page}&per_page=${perPage}`,
      ),
    enabled: !!tripId,
  });
}

export function useCreateWatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PriceWatchCreateRequest) =>
      api.post<ApiResponse<PriceWatch>>("/api/v1/watches/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watches"] });
      queryClient.invalidateQueries({ queryKey: ["tripWatches"] });
      toast.success("Price watch created");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useUpdateWatch(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PriceWatchUpdateRequest) =>
      api.patch<ApiResponse<PriceWatch>>(`/api/v1/watches/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watches"] });
      queryClient.invalidateQueries({ queryKey: ["tripWatches"] });
      queryClient.invalidateQueries({ queryKey: ["watch", id] });
      toast.success("Price watch updated");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useDeleteWatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/watches/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watches"] });
      queryClient.invalidateQueries({ queryKey: ["tripWatches"] });
      toast.success("Price watch deleted");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}
