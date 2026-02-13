import { useMemo } from "react";
import airports from "@/data/airports.json";

export interface Airport {
  code: string;
  name: string;
  city: string;
  country: string;
}

export function useAirportSearch(query: string): Airport[] {
  return useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length === 0) return [];

    return (airports as Airport[]).filter(
      (a) =>
        a.code.toLowerCase().includes(q) ||
        a.name.toLowerCase().includes(q) ||
        a.city.toLowerCase().includes(q),
    ).slice(0, 10);
  }, [query]);
}
