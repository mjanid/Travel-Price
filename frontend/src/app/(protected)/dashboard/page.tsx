"use client";

import { useCurrentUser } from "@/hooks/use-auth";
import { useTrips } from "@/hooks/use-trips";
import { useWatches } from "@/hooks/use-watches";
import { useAlerts } from "@/hooks/use-alerts";
import { TripCard } from "@/components/trips/trip-card";
import { AlertList } from "@/components/alerts/alert-list";
import { Card } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const { data: user } = useCurrentUser();
  const { data: tripsData, isLoading: tripsLoading } = useTrips(1, 4);
  const { data: watchesData } = useWatches(1, 1);
  const { data: alertsData } = useAlerts(1, 1);

  const trips = tripsData?.data ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Welcome{user ? `, ${user.full_name}` : ""}
        </h1>
        <p className="mt-1 text-sm text-muted">
          Track travel prices and get notified when they drop.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-muted">Total Trips</p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {tripsData?.meta?.total ?? 0}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Active Watches</p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {watchesData?.meta?.total ?? 0}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">Alerts Sent</p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {alertsData?.meta?.total ?? 0}
          </p>
        </Card>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            Recent Trips
          </h2>
          <Link href="/trips">
            <Button variant="secondary" size="sm">
              View all
            </Button>
          </Link>
        </div>

        {tripsLoading ? (
          <p className="text-sm text-muted">Loading...</p>
        ) : trips.length === 0 ? (
          <Card>
            <p className="text-sm text-muted">
              No trips yet.{" "}
              <Link href="/trips/new" className="text-primary hover:underline">
                Create your first trip
              </Link>{" "}
              to start tracking prices.
            </p>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {trips.map((trip) => (
              <TripCard key={trip.id} trip={trip} />
            ))}
          </div>
        )}
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">
          Recent Alerts
        </h2>
        <AlertList />
      </div>
    </div>
  );
}
