"use client";

import { useState } from "react";
import { useTripWatches } from "@/hooks/use-watches";
import { WatchCard } from "./watch-card";
import { WatchForm } from "./watch-form";
import { Button } from "@/components/ui/button";
import { CardSkeleton } from "@/components/ui/skeleton";

interface WatchListProps {
  tripId: string;
}

export function WatchList({ tripId }: WatchListProps) {
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading, error } = useTripWatches(tripId);

  const watches = data?.data ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-foreground">Price Watches</h2>
        <Button size="sm" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add Watch"}
        </Button>
      </div>

      {showForm && (
        <WatchForm tripId={tripId} onSuccess={() => setShowForm(false)} />
      )}

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <p className="text-sm text-danger">Failed to load watches.</p>
      ) : watches.length === 0 ? (
        <p className="text-sm text-muted">
          No price watches yet. Add one to start monitoring prices.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {watches.map((watch) => (
            <WatchCard key={watch.id} watch={watch} />
          ))}
        </div>
      )}
    </div>
  );
}
