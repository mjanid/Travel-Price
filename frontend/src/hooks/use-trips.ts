"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import type {
  ApiResponse,
  PaginatedResponse,
  Trip,
  TripCreateRequest,
  TripUpdateRequest,
} from "@/lib/types";
import {
  apiResponseSchema,
  paginatedResponseSchema,
  tripResponseSchema,
} from "@/lib/validators";

const tripListSchema = paginatedResponseSchema(tripResponseSchema);
const tripDetailSchema = apiResponseSchema(tripResponseSchema);

export function useTrips(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["trips", page, perPage],
    queryFn: async () => {
      const raw = await api.get<PaginatedResponse<Trip>>(
        `/api/v1/trips/?page=${page}&per_page=${perPage}`,
      );
      return tripListSchema.parse(raw) as PaginatedResponse<Trip>;
    },
  });
}

export function useTrip(id: string) {
  return useQuery({
    queryKey: ["trip", id],
    queryFn: async () => {
      const raw = await api.get<ApiResponse<Trip>>(`/api/v1/trips/${id}`);
      return tripDetailSchema.parse(raw) as ApiResponse<Trip>;
    },
    enabled: !!id,
  });
}

export function useCreateTrip() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: async (data: TripCreateRequest) => {
      const raw = await api.post<ApiResponse<Trip>>("/api/v1/trips/", data);
      return tripDetailSchema.parse(raw) as ApiResponse<Trip>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      toast.success("Trip created successfully");
      router.push("/trips");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useUpdateTrip(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TripUpdateRequest) => {
      const raw = await api.patch<ApiResponse<Trip>>(`/api/v1/trips/${id}`, data);
      return tripDetailSchema.parse(raw) as ApiResponse<Trip>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["trip", id] });
      toast.success("Trip updated successfully");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}

export function useDeleteTrip() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/trips/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      toast.success("Trip deleted");
      router.push("/trips");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}
