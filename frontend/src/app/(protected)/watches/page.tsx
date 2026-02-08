"use client";

import { useState } from "react";
import { useWatches } from "@/hooks/use-watches";
import { WatchCard } from "@/components/watches/watch-card";
import { Button } from "@/components/ui/button";

export default function WatchesPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useWatches(page);

  const watches = data?.data ?? [];
  const meta = data?.meta;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Price Watches</h1>

      {isLoading ? (
        <p className="text-sm text-muted">Loading watches...</p>
      ) : error ? (
        <p className="text-sm text-danger">Failed to load watches.</p>
      ) : watches.length === 0 ? (
        <p className="text-sm text-muted">
          No price watches yet. Create a watch from a trip detail page.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {watches.map((watch) => (
            <WatchCard key={watch.id} watch={watch} />
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
