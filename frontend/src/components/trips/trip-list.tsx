"use client";

import { useState } from "react";
import Link from "next/link";
import { useTrips } from "@/hooks/use-trips";
import { TripCard } from "./trip-card";
import { Button } from "@/components/ui/button";

export function TripList() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useTrips(page);

  if (isLoading) {
    return <p className="text-sm text-muted">Loading trips...</p>;
  }

  if (error) {
    return (
      <p className="text-sm text-danger">
        Failed to load trips: {error.message}
      </p>
    );
  }

  const trips = data?.data ?? [];
  const meta = data?.meta;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Your Trips</h2>
        <Link href="/trips/new">
          <Button size="sm">New Trip</Button>
        </Link>
      </div>

      {trips.length === 0 ? (
        <p className="text-sm text-muted">
          No trips yet. Create your first trip to start tracking prices.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {trips.map((trip) => (
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
