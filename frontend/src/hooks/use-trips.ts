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

export function useTrips(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["trips", page, perPage],
    queryFn: () =>
      api.get<PaginatedResponse<Trip>>(
        `/api/v1/trips/?page=${page}&per_page=${perPage}`,
      ),
  });
}

export function useTrip(id: string) {
  return useQuery({
    queryKey: ["trip", id],
    queryFn: () => api.get<ApiResponse<Trip>>(`/api/v1/trips/${id}`),
    enabled: !!id,
  });
}

export function useCreateTrip() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (data: TripCreateRequest) =>
      api.post<ApiResponse<Trip>>("/api/v1/trips/", data),
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
    mutationFn: (data: TripUpdateRequest) =>
      api.patch<ApiResponse<Trip>>(`/api/v1/trips/${id}`, data),
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
