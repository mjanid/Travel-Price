export function formatPrice(cents: number, currency = "USD"): string {
  const dollars = cents / 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(dollars);
}

export function formatDate(iso: string): string {
  // Dates without time component are parsed as UTC midnight to avoid timezone shifts
  const date = iso.includes("T") ? new Date(iso) : new Date(iso + "T00:00:00Z");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function classNames(...classes: (string | false | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

export interface AggregatedPricePoint {
  date: string;
  fullDate: string;
  min: number;
  max: number;
  avg: number;
  count: number;
}

export function aggregateSnapshots(
  snapshots: { scraped_at: string; price: number }[],
): AggregatedPricePoint[] {
  if (snapshots.length === 0) return [];

  const groups = new Map<string, { prices: number[]; scraped_at: string }>();

  for (const s of snapshots) {
    // Group by minute-level timestamp
    const key = s.scraped_at.slice(0, 16); // "2026-02-12T15:30"
    const group = groups.get(key);
    if (group) {
      group.prices.push(s.price);
    } else {
      groups.set(key, { prices: [s.price], scraped_at: s.scraped_at });
    }
  }

  const points: AggregatedPricePoint[] = [];
  for (const [, group] of groups) {
    const prices = group.prices;
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const avg = Math.round(prices.reduce((a, b) => a + b, 0) / prices.length);
    const d = new Date(group.scraped_at);
    points.push({
      date: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      fullDate: group.scraped_at,
      min: min / 100,
      max: max / 100,
      avg: avg / 100,
      count: prices.length,
    });
  }

  return points.sort(
    (a, b) => new Date(a.fullDate).getTime() - new Date(b.fullDate).getTime(),
  );
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "--";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
    timeZone: "UTC",
  });
}

export function formatStops(stops: number | null | undefined): string {
  if (stops === null || stops === undefined) return "--";
  if (stops === 0) return "Nonstop";
  if (stops === 1) return "1 stop";
  return `${stops} stops`;
}

export function buildGoogleFlightsUrl(
  trip: {
    origin: string;
    destination: string;
    departure_date: string;
    return_date?: string | null;
    travelers?: number;
  },
  cabinClass?: string,
): string {
  let q = `flights from ${trip.origin} to ${trip.destination} on ${trip.departure_date}`;
  if (trip.return_date) {
    q += ` returning ${trip.return_date}`;
  }
  if (trip.travelers && trip.travelers > 1) {
    q += ` ${trip.travelers} passengers`;
  }
  if (cabinClass && cabinClass !== "economy") {
    q += ` ${cabinClass}`;
  }

  const params = new URLSearchParams({ q, curr: "USD", hl: "en" });
  return `https://www.google.com/travel/flights?${params.toString()}`;
}
