"use client";

import { useRouter } from "next/navigation";
import { useCurrentUser } from "@/hooks/use-auth";
import { useTrips } from "@/hooks/use-trips";
import { useWatches } from "@/hooks/use-watches";
import { useAlerts } from "@/hooks/use-alerts";
import { TripCard } from "@/components/trips/trip-card";
import { AlertList } from "@/components/alerts/alert-list";
import { StatCard } from "@/components/dashboard/stat-card";
import { Card } from "@/components/ui/card";
import { StatSkeleton, CardSkeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const { data: tripsData, isLoading: tripsLoading } = useTrips(1, 4);
  const { data: watchesData, isLoading: watchesLoading } = useWatches(1, 1);
  const { data: alertsData, isLoading: alertsLoading } = useAlerts(1, 1);

  const trips = tripsData?.data ?? [];
  const statsLoading = tripsLoading || watchesLoading || alertsLoading;

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

      {statsLoading ? (
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <StatSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Total Trips" value={tripsData?.meta?.total ?? 0} />
          <StatCard
            label="Active Watches"
            value={watchesData?.meta?.total ?? 0}
          />
          <StatCard
            label="Alerts Sent"
            value={alertsData?.meta?.total ?? 0}
          />
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card
          hover
          onClick={() => router.push("/trips/new")}
          className="cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-primary">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-foreground">New Trip</p>
              <p className="text-xs text-muted">Start tracking prices</p>
            </div>
          </div>
        </Card>
        <Card
          hover
          onClick={() => router.push("/watches")}
          className="cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-50 text-success">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-foreground">Manage Watches</p>
              <p className="text-xs text-muted">Set price alerts</p>
            </div>
          </div>
        </Card>
        <Card
          hover
          onClick={() => router.push("/trips")}
          className="cursor-pointer"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-primary">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-foreground">View All Trips</p>
              <p className="text-xs text-muted">Browse your trips</p>
            </div>
          </div>
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
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
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
