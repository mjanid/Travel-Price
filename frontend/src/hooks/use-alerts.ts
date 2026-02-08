"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PaginatedResponse, Alert } from "@/lib/types";

export function useAlerts(page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["alerts", page, perPage],
    queryFn: () =>
      api.get<PaginatedResponse<Alert>>(
        `/api/v1/alerts/?page=${page}&per_page=${perPage}`,
      ),
  });
}

export function useWatchAlerts(watchId: string, page = 1, perPage = 20) {
  return useQuery({
    queryKey: ["watchAlerts", watchId, page, perPage],
    queryFn: () =>
      api.get<PaginatedResponse<Alert>>(
        `/api/v1/watches/${watchId}/alerts?page=${page}&per_page=${perPage}`,
      ),
    enabled: !!watchId,
  });
}
