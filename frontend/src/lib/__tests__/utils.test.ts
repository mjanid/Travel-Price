import { describe, it, expect } from "vitest";
import { formatPrice, formatDate, classNames } from "../utils";

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
