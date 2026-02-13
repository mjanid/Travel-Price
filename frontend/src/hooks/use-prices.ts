"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "@/lib/toast";
import type {
  ApiResponse,
  PaginatedResponse,
  PriceSnapshot,
} from "@/lib/types";

export function usePriceHistory(
  tripId: string,
  provider?: string,
  page = 1,
  perPage = 100,
) {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (provider) params.set("provider", provider);

  return useQuery({
    queryKey: ["priceHistory", tripId, provider, page, perPage],
    queryFn: () =>
      api.get<PaginatedResponse<PriceSnapshot>>(
        `/api/v1/trips/${tripId}/prices?${params}`,
      ),
    enabled: !!tripId,
  });
}

export function useScrapeTrip(tripId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (opts?: { provider?: string; cabin_class?: string }) =>
      api.post<ApiResponse<PriceSnapshot[]>>(
        `/api/v1/trips/${tripId}/scrape`,
        opts,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["priceHistory", tripId] });
      toast.success("Scrape completed");
    },
    onError: (err: Error) => toast.error(err.message),
  });
}
