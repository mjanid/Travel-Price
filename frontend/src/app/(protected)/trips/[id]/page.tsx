"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useTrip, useDeleteTrip } from "@/hooks/use-trips";
import { useScrapeTrip } from "@/hooks/use-prices";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { PriceChart } from "@/components/charts/price-chart";
import { FlightResultsTable } from "@/components/flights/flight-results-table";
import { WatchList } from "@/components/watches/watch-list";
import { formatDate, buildGoogleFlightsUrl } from "@/lib/utils";

export default function TripDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isLoading, error } = useTrip(id);
  const deleteTrip = useDeleteTrip();
  const scrapeTrip = useScrapeTrip(id);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-8">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-1">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-5 w-32" />
              </div>
            ))}
          </div>
        </div>
        <div className="flex gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-9 w-24 rounded-lg" />
          ))}
        </div>
      </div>
    );
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
  const isFlight = trip.trip_type === "flight";

  const tripTypeLabels: Record<string, string> = {
    flight: "Flight",
    hotel: "Hotel",
    car_rental: "Car Rental",
  };

  function handleDeleteConfirm() {
    deleteTrip.mutate(id);
    setShowDeleteConfirm(false);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-foreground">
            {trip.origin} &rarr; {trip.destination}
          </h1>
          <Badge variant="default">
            {tripTypeLabels[trip.trip_type] ?? trip.trip_type}
          </Badge>
        </div>
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

      <div className="flex flex-wrap gap-3">
        <Button
          variant="secondary"
          onClick={() => router.push(`/trips/${id}/edit`)}
        >
          Edit
        </Button>
        <Button
          onClick={() => scrapeTrip.mutate({})}
          loading={scrapeTrip.isPending}
        >
          Scrape Now
        </Button>
        {isFlight && (
          <Button
            variant="secondary"
            onClick={() =>
              window.open(buildGoogleFlightsUrl(trip), "_blank", "noopener")
            }
          >
            Search on Google Flights
          </Button>
        )}
        <Button
          variant="danger"
          onClick={() => setShowDeleteConfirm(true)}
          loading={deleteTrip.isPending}
        >
          Delete
        </Button>
        <Button variant="secondary" onClick={() => router.back()}>
          Back
        </Button>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">
          Price History
        </h2>
        <Card>
          <PriceChart tripId={id} />
        </Card>
      </div>

      {isFlight && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">
            Flight Results
          </h2>
          <FlightResultsTable tripId={id} trip={trip} />
        </div>
      )}

      <WatchList tripId={id} />

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Trip"
        message="Are you sure you want to delete this trip? All associated price watches, price history, and alerts will be permanently removed."
        confirmText="Delete"
        variant="danger"
        loading={deleteTrip.isPending}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
