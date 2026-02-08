import { describe, it, expect } from "vitest";
import {
  loginSchema,
  registerSchema,
  tripCreateSchema,
  priceWatchCreateSchema,
} from "../validators";

describe("loginSchema", () => {
  it("validates correct input", () => {
    const result = loginSchema.safeParse({
      email: "test@example.com",
      password: "password123",
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid email", () => {
    const result = loginSchema.safeParse({
      email: "not-an-email",
      password: "password123",
    });
    expect(result.success).toBe(false);
  });

  it("rejects short password", () => {
    const result = loginSchema.safeParse({
      email: "test@example.com",
      password: "short",
    });
    expect(result.success).toBe(false);
  });
});

describe("registerSchema", () => {
  it("validates correct input", () => {
    const result = registerSchema.safeParse({
      email: "test@example.com",
      password: "password123",
      full_name: "Test User",
    });
    expect(result.success).toBe(true);
  });

  it("rejects missing full_name", () => {
    const result = registerSchema.safeParse({
      email: "test@example.com",
      password: "password123",
    });
    expect(result.success).toBe(false);
  });
});

describe("tripCreateSchema", () => {
  it("validates correct input", () => {
    const result = tripCreateSchema.safeParse({
      origin: "JFK",
      destination: "LAX",
      departure_date: "2025-06-15",
      return_date: "2025-06-20",
      travelers: 2,
    });
    expect(result.success).toBe(true);
  });

  it("rejects return date before departure date", () => {
    const result = tripCreateSchema.safeParse({
      origin: "JFK",
      destination: "LAX",
      departure_date: "2025-06-20",
      return_date: "2025-06-15",
      travelers: 2,
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid IATA code", () => {
    const result = tripCreateSchema.safeParse({
      origin: "TOOLONG",
      destination: "LAX",
      departure_date: "2025-06-15",
      return_date: "2025-06-20",
      travelers: 1,
    });
    expect(result.success).toBe(false);
  });
});

describe("priceWatchCreateSchema", () => {
  it("validates correct input", () => {
    const result = priceWatchCreateSchema.safeParse({
      trip_id: "550e8400-e29b-41d4-a716-446655440000",
      target_price: 250,
    });
    expect(result.success).toBe(true);
  });

  it("applies defaults for provider and cooldown", () => {
    const result = priceWatchCreateSchema.safeParse({
      trip_id: "550e8400-e29b-41d4-a716-446655440000",
      target_price: 100,
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.provider).toBe("google_flights");
      expect(result.data.alert_cooldown_hours).toBe(6);
    }
  });

  it("rejects zero target price", () => {
    const result = priceWatchCreateSchema.safeParse({
      trip_id: "550e8400-e29b-41d4-a716-446655440000",
      target_price: 0,
    });
    expect(result.success).toBe(false);
  });

  it("rejects negative target price", () => {
    const result = priceWatchCreateSchema.safeParse({
      trip_id: "550e8400-e29b-41d4-a716-446655440000",
      target_price: -50,
    });
    expect(result.success).toBe(false);
  });

  it("rejects missing trip_id", () => {
    const result = priceWatchCreateSchema.safeParse({
      target_price: 250,
    });
    expect(result.success).toBe(false);
  });
});
