"use client";

import { useState, useMemo } from "react";
import { useWatches } from "@/hooks/use-watches";
import { WatchCard } from "@/components/watches/watch-card";
import { CardSkeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { classNames } from "@/lib/utils";

type WatchFilter = "all" | "active" | "paused";

const filterTabs: { key: WatchFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "paused", label: "Paused" },
];

export default function WatchesPage() {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<WatchFilter>("all");
  const { data, isLoading, error } = useWatches(page);

  const watches = useMemo(() => data?.data ?? [], [data]);
  const meta = data?.meta;

  const filtered = useMemo(() => {
    if (filter === "all") return watches;
    if (filter === "active") return watches.filter((w) => w.is_active);
    return watches.filter((w) => !w.is_active);
  }, [watches, filter]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Price Watches</h1>

      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {filterTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={classNames(
              "rounded-md px-4 py-1.5 text-sm font-medium transition-colors",
              filter === tab.key
                ? "bg-white text-foreground shadow-sm"
                : "text-muted hover:text-foreground",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : error ? (
        <p className="text-sm text-danger">Failed to load watches.</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-muted">
          {filter === "all"
            ? "No price watches yet. Create a watch from a trip detail page."
            : `No ${filter} watches.`}
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((watch) => (
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
