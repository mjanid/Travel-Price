"use client";

import { usePriceHistory } from "@/hooks/use-prices";
import { Card } from "@/components/ui/card";
import {
  formatPrice,
  formatTime,
  formatStops,
  buildGoogleFlightsUrl,
  formatDate,
} from "@/lib/utils";
import type { PriceSnapshot, Trip } from "@/lib/types";

interface FlightResultsTableProps {
  tripId: string;
  trip: Trip;
}

export function FlightResultsTable({ tripId, trip }: FlightResultsTableProps) {
  const { data, isLoading, error } = usePriceHistory(tripId);

  if (isLoading) {
    return <p className="text-sm text-muted">Loading flight results...</p>;
  }

  if (error) {
    return (
      <p className="text-sm text-danger">Failed to load flight results.</p>
    );
  }

  const snapshots = data?.data ?? [];
  if (snapshots.length === 0) {
    return (
      <p className="text-sm text-muted">
        No flight results yet. Run a scrape to see results.
      </p>
    );
  }

  // Find latest scrape timestamp and filter to only those results
  const latestTimestamp = snapshots.reduce((latest, s) => {
    return s.scraped_at > latest ? s.scraped_at : latest;
  }, snapshots[0].scraped_at);

  // Match by minute-level timestamp (same grouping as aggregateSnapshots)
  const latestKey = latestTimestamp.slice(0, 16);
  const latestResults = snapshots
    .filter((s) => s.scraped_at.slice(0, 16) === latestKey)
    .sort((a, b) => a.price - b.price);

  if (latestResults.length === 0) {
    return null;
  }

  const cheapestPrice = latestResults[0].price;
  const scrapedDate = new Date(latestTimestamp);
  const scrapedLabel = scrapedDate.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }) + " at " + scrapedDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold text-foreground">Latest Flight Results</h3>
        <span className="text-xs text-muted">Last scraped: {scrapedLabel}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="pb-2 pr-4 font-medium">Airline</th>
              <th className="pb-2 pr-4 font-medium">Departure</th>
              <th className="pb-2 pr-4 font-medium">Arrival</th>
              <th className="pb-2 pr-4 font-medium">Stops</th>
              <th className="pb-2 pr-4 font-medium text-right">Price</th>
              <th className="pb-2 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {latestResults.map((flight) => (
              <FlightRow
                key={flight.id}
                flight={flight}
                trip={trip}
                isCheapest={flight.price === cheapestPrice}
              />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function getRawDataField(raw: string | null, field: string): string | null {
  if (!raw) return null;
  try {
    const data = JSON.parse(raw);
    return data[field] ?? null;
  } catch {
    return null;
  }
}

function FlightRow({
  flight,
  trip,
  isCheapest,
}: {
  flight: PriceSnapshot;
  trip: Trip;
  isCheapest: boolean;
}) {
  const searchUrl = buildGoogleFlightsUrl(trip, flight.cabin_class ?? undefined);
  const depTime = flight.outbound_departure
    ? formatTime(flight.outbound_departure)
    : getRawDataField(flight.raw_data, "departure_time") ?? "--";
  const arrTime = flight.outbound_arrival
    ? formatTime(flight.outbound_arrival)
    : getRawDataField(flight.raw_data, "arrival_time") ?? "--";

  return (
    <tr
      className={
        isCheapest
          ? "border-b border-border bg-green-50"
          : "border-b border-border"
      }
    >
      <td className="py-3 pr-4 font-medium text-foreground">
        {flight.airline ?? "--"}
      </td>
      <td className="py-3 pr-4 text-foreground">
        {depTime}
      </td>
      <td className="py-3 pr-4 text-foreground">
        {arrTime}
      </td>
      <td className="py-3 pr-4 text-foreground">
        {formatStops(flight.stops)}
      </td>
      <td className="py-3 pr-4 text-right font-semibold text-foreground">
        {isCheapest && (
          <span className="mr-1 text-xs text-green-600">Lowest</span>
        )}
        {formatPrice(flight.price, flight.currency)}
      </td>
      <td className="py-3">
        <a
          href={searchUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
        >
          Search &rarr;
        </a>
      </td>
    </tr>
  );
}
