"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, Alert } from "@/lib/types";
import { paginatedResponseSchema, alertResponseSchema } from "@/lib/validators";

const alertListSchema = paginatedResponseSchema(alertResponseSchema);

export function useAlerts(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["alerts", page, perPage],
    queryFn: async () => {
      const raw = await api.get<PaginatedResponse<Alert>>(
        `/api/v1/alerts/?page=${page}&per_page=${perPage}`,
      );
      return alertListSchema.parse(raw) as PaginatedResponse<Alert>;
    },
  });
}

export function useWatchAlerts(watchId: string, page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["watchAlerts", watchId, page, perPage],
    queryFn: async () => {
      const raw = await api.get<PaginatedResponse<Alert>>(
        `/api/v1/watches/${watchId}/alerts?page=${page}&per_page=${perPage}`,
      );
      return alertListSchema.parse(raw) as PaginatedResponse<Alert>;
    },
    enabled: !!watchId,
  });
}
