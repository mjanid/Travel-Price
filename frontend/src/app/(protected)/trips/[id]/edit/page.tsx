"use client";

import { use } from "react";
import { useTrip } from "@/hooks/use-trips";
import { TripForm } from "@/components/trips/trip-form";

export default function EditTripPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data, isLoading, error } = useTrip(id);

  if (isLoading) {
    return <p className="text-sm text-muted">Loading trip...</p>;
  }

  if (error || !data) {
    return (
      <p className="text-sm text-danger">
        Failed to load trip: {error?.message ?? "Not found"}
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Edit Trip</h1>
      <TripForm trip={data.data ?? undefined} />
    </div>
  );
}
