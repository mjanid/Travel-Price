"use client";

import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import type { Trip } from "@/lib/types";

interface TripCardProps {
  trip: Trip;
}

export function TripCard({ trip }: TripCardProps) {
  const router = useRouter();

  const endDate = trip.return_date ?? trip.departure_date;
  const isPast = new Date(endDate) < new Date();

  return (
    <Card hover onClick={() => router.push(`/trips/${trip.id}`)}>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-foreground">
            {trip.origin} &rarr; {trip.destination}
          </h3>
          <p className="mt-1 text-sm text-muted">
            {formatDate(trip.departure_date)}
            {trip.return_date ? ` – ${formatDate(trip.return_date)}` : ""}
          </p>
          <p className="mt-1 text-sm text-muted">
            {trip.travelers} traveler{trip.travelers !== 1 ? "s" : ""}
          </p>
        </div>
        <Badge variant={isPast ? "danger" : "success"}>
          {isPast ? "Past" : "Upcoming"}
        </Badge>
      </div>
    </Card>
  );
}
