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
import {
  apiResponseSchema,
  paginatedResponseSchema,
  priceWatchResponseSchema,
} from "@/lib/validators";

const watchListSchema = paginatedResponseSchema(priceWatchResponseSchema);
const watchDetailSchema = apiResponseSchema(priceWatchResponseSchema);

export function useWatches(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["watches", page, perPage],
    queryFn: async () => {
      const raw = await api.get<PaginatedResponse<PriceWatch>>(
        `/api/v1/watches/?page=${page}&per_page=${perPage}`,
      );
      return watchListSchema.parse(raw) as PaginatedResponse<PriceWatch>;
    },
  });
}

export function useWatch(id: string) {
  return useQuery({
    queryKey: ["watch", id],
    queryFn: async () => {
      const raw = await api.get<ApiResponse<PriceWatch>>(`/api/v1/watches/${id}`);
      return watchDetailSchema.parse(raw) as ApiResponse<PriceWatch>;
    },
    enabled: !!id,
  });
}

export function useTripWatches(tripId: string, page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["tripWatches", tripId, page, perPage],
    queryFn: async () => {
      const raw = await api.get<PaginatedResponse<PriceWatch>>(
        `/api/v1/trips/${tripId}/watches?page=${page}&per_page=${perPage}`,
      );
      return watchListSchema.parse(raw) as PaginatedResponse<PriceWatch>;
    },
    enabled: !!tripId,
  });
}

export function useCreateWatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PriceWatchCreateRequest) => {
      const raw = await api.post<ApiResponse<PriceWatch>>("/api/v1/watches/", data);
      return watchDetailSchema.parse(raw) as ApiResponse<PriceWatch>;
    },
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
    mutationFn: async (data: PriceWatchUpdateRequest) => {
      const raw = await api.patch<ApiResponse<PriceWatch>>(`/api/v1/watches/${id}`, data);
      return watchDetailSchema.parse(raw) as ApiResponse<PriceWatch>;
    },
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
