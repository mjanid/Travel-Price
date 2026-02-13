"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useTrips } from "@/hooks/use-trips";
import { TripCard } from "./trip-card";
import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";
import { CardSkeleton } from "@/components/ui/skeleton";
import { classNames } from "@/lib/utils";

type StatusFilter = "all" | "upcoming" | "past";

export function TripList() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const { data, isLoading, error } = useTrips(page);

  const trips = useMemo(() => data?.data ?? [], [data]);
  const meta = data?.meta;

  const filteredTrips = useMemo(() => {
    return trips.filter((trip) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        trip.origin.toLowerCase().includes(q) ||
        trip.destination.toLowerCase().includes(q);

      if (!matchesSearch) return false;

      if (statusFilter === "all") return true;
      const endDate = trip.return_date ?? trip.departure_date;
      const isPast = new Date(endDate) < new Date();
      return statusFilter === "past" ? isPast : !isPast;
    });
  }, [trips, searchQuery, statusFilter]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="h-6 w-32 animate-pulse rounded bg-gray-200" />
          <div className="h-8 w-20 animate-pulse rounded-lg bg-gray-200" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-sm text-danger">
        Failed to load trips: {error.message}
      </p>
    );
  }

  const statusTabs: { value: StatusFilter; label: string }[] = [
    { value: "all", label: "All" },
    { value: "upcoming", label: "Upcoming" },
    { value: "past", label: "Past" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Your Trips</h2>
        <Link href="/trips/new">
          <Button size="sm">New Trip</Button>
        </Link>
      </div>

      {trips.length > 0 && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search by origin or destination..."
            className="sm:w-64"
          />
          <div className="flex gap-1">
            {statusTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setStatusFilter(tab.value)}
                className={classNames(
                  "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  statusFilter === tab.value
                    ? "bg-primary text-white"
                    : "text-muted hover:bg-card-hover",
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {trips.length === 0 ? (
        <p className="text-sm text-muted">
          No trips yet. Create your first trip to start tracking prices.
        </p>
      ) : filteredTrips.length === 0 ? (
        <p className="text-sm text-muted">
          No trips match your search.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {filteredTrips.map((trip) => (
            <TripCard key={trip.id} trip={trip} />
          ))}
        </div>
      )}

      {meta && meta.total_pages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted">
            Page {meta.page} of {meta.total_pages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= meta.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
