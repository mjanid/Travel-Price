import { describe, it, expect } from "vitest";
import {
  formatPrice,
  formatDate,
  classNames,
  aggregateSnapshots,
  formatTime,
  formatStops,
  buildGoogleFlightsUrl,
} from "../utils";

describe("formatPrice", () => {
  it("formats cents to dollar string", () => {
    expect(formatPrice(12345)).toBe("$123.45");
  });

  it("formats zero", () => {
    expect(formatPrice(0)).toBe("$0.00");
  });

  it("formats small amounts", () => {
    expect(formatPrice(5)).toBe("$0.05");
  });

  it("uses custom currency", () => {
    expect(formatPrice(10000, "EUR")).toBe("€100.00");
  });
});

describe("formatDate", () => {
  it("formats ISO date string", () => {
    const result = formatDate("2025-06-15");
    expect(result).toContain("2025");
  });

  it("handles datetime strings", () => {
    const result = formatDate("2025-06-15T10:30:00Z");
    expect(result).toContain("2025");
  });
});

describe("classNames", () => {
  it("joins class strings", () => {
    expect(classNames("a", "b", "c")).toBe("a b c");
  });

  it("filters falsy values", () => {
    expect(classNames("a", undefined, false, "b", null, "")).toBe("a b");
  });

  it("returns empty string for no args", () => {
    expect(classNames()).toBe("");
  });
});

describe("aggregateSnapshots", () => {
  it("returns empty array for empty input", () => {
    expect(aggregateSnapshots([])).toEqual([]);
  });

  it("aggregates a single scrape with multiple flights into one point", () => {
    const snapshots = [
      { scraped_at: "2026-02-12T15:30:00Z", price: 10000 },
      { scraped_at: "2026-02-12T15:30:05Z", price: 15000 },
      { scraped_at: "2026-02-12T15:30:10Z", price: 20000 },
    ];
    const result = aggregateSnapshots(snapshots);
    expect(result).toHaveLength(1);
    expect(result[0].min).toBe(100);
    expect(result[0].max).toBe(200);
    expect(result[0].avg).toBe(150);
    expect(result[0].count).toBe(3);
  });

  it("separates scrapes at different timestamps", () => {
    const snapshots = [
      { scraped_at: "2026-02-12T10:00:00Z", price: 10000 },
      { scraped_at: "2026-02-12T10:00:05Z", price: 12000 },
      { scraped_at: "2026-02-12T14:00:00Z", price: 8000 },
      { scraped_at: "2026-02-12T14:00:05Z", price: 9000 },
    ];
    const result = aggregateSnapshots(snapshots);
    expect(result).toHaveLength(2);
    // Should be sorted chronologically
    expect(result[0].min).toBe(100);
    expect(result[1].min).toBe(80);
  });
});

describe("formatTime", () => {
  it("returns -- for null", () => {
    expect(formatTime(null)).toBe("--");
  });

  it("returns -- for undefined", () => {
    expect(formatTime(undefined)).toBe("--");
  });

  it("formats AM time", () => {
    const result = formatTime("2026-02-12T07:10:00Z");
    expect(result).toMatch(/7:10\s*AM/);
  });

  it("formats PM time", () => {
    const result = formatTime("2026-02-12T15:45:00Z");
    expect(result).toMatch(/3:45\s*PM/);
  });

  it("formats noon", () => {
    const result = formatTime("2026-02-12T12:00:00Z");
    expect(result).toMatch(/12:00\s*PM/);
  });

  it("formats midnight", () => {
    const result = formatTime("2026-02-12T00:00:00Z");
    expect(result).toMatch(/12:00\s*AM/);
  });
});

describe("formatStops", () => {
  it("returns -- for null", () => {
    expect(formatStops(null)).toBe("--");
  });

  it("returns -- for undefined", () => {
    expect(formatStops(undefined)).toBe("--");
  });

  it("returns Nonstop for 0", () => {
    expect(formatStops(0)).toBe("Nonstop");
  });

  it("returns 1 stop for 1", () => {
    expect(formatStops(1)).toBe("1 stop");
  });

  it("returns N stops for 2+", () => {
    expect(formatStops(2)).toBe("2 stops");
    expect(formatStops(3)).toBe("3 stops");
  });
});

describe("buildGoogleFlightsUrl", () => {
  it("builds URL for one-way trip", () => {
    const url = buildGoogleFlightsUrl({
      origin: "VIE",
      destination: "BER",
      departure_date: "2026-02-14",
    });
    expect(url).toContain("google.com/travel/flights");
    expect(url).toContain("VIE");
    expect(url).toContain("BER");
    expect(url).toContain("2026-02-14");
    expect(url).not.toContain("returning");
  });

  it("builds URL for round-trip", () => {
    const url = buildGoogleFlightsUrl({
      origin: "VIE",
      destination: "BER",
      departure_date: "2026-02-14",
      return_date: "2026-02-21",
    });
    expect(url).toContain("returning");
    expect(url).toContain("2026-02-21");
  });

  it("includes passengers when more than 1", () => {
    const url = buildGoogleFlightsUrl({
      origin: "VIE",
      destination: "BER",
      departure_date: "2026-02-14",
      travelers: 3,
    });
    expect(url).toContain("3+passengers");
  });

  it("does not include passengers for 1 traveler", () => {
    const url = buildGoogleFlightsUrl({
      origin: "VIE",
      destination: "BER",
      departure_date: "2026-02-14",
      travelers: 1,
    });
    expect(url).not.toContain("passengers");
  });

  it("includes cabin class when not economy", () => {
    const url = buildGoogleFlightsUrl(
      {
        origin: "VIE",
        destination: "BER",
        departure_date: "2026-02-14",
      },
      "business",
    );
    expect(url).toContain("business");
  });
});
