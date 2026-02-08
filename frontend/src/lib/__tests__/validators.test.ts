import { describe, it, expect } from "vitest";
import { loginSchema, registerSchema, tripCreateSchema } from "../validators";

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
