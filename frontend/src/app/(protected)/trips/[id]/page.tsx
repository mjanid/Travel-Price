"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { useTrip, useDeleteTrip } from "@/hooks/use-trips";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

export default function TripDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isLoading, error } = useTrip(id);
  const deleteTrip = useDeleteTrip();

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

  const trip = data.data!;
  const endDate = trip.return_date ?? trip.departure_date;
  const isPast = new Date(endDate) < new Date();

  function handleDelete() {
    if (!confirm("Are you sure you want to delete this trip?")) return;
    deleteTrip.mutate(id, {
      onSuccess: () => router.push("/trips"),
    });
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">
          {trip.origin} &rarr; {trip.destination}
        </h1>
        <Badge variant={isPast ? "danger" : "success"}>
          {isPast ? "Past" : "Upcoming"}
        </Badge>
      </div>

      <Card>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-muted">Origin</dt>
            <dd className="font-medium text-foreground">{trip.origin}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Destination</dt>
            <dd className="font-medium text-foreground">{trip.destination}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Departure Date</dt>
            <dd className="font-medium text-foreground">
              {formatDate(trip.departure_date)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Return Date</dt>
            <dd className="font-medium text-foreground">
              {trip.return_date ? formatDate(trip.return_date) : "One-way"}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Travelers</dt>
            <dd className="font-medium text-foreground">{trip.travelers}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Created</dt>
            <dd className="font-medium text-foreground">
              {formatDate(trip.created_at)}
            </dd>
          </div>
        </dl>
      </Card>

      <div className="flex gap-3">
        <Button
          variant="secondary"
          onClick={() => router.push(`/trips/${id}/edit`)}
        >
          Edit
        </Button>
        <Button
          variant="danger"
          onClick={handleDelete}
          loading={deleteTrip.isPending}
        >
          Delete
        </Button>
        <Button variant="secondary" onClick={() => router.back()}>
          Back
        </Button>
      </div>
    </div>
  );
}
