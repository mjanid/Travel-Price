import { z } from "zod/v4";

export const loginSchema = z.object({
  email: z.email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export const registerSchema = z.object({
  email: z.email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  full_name: z.string().min(1, "Full name is required").max(255),
});

export const tripCreateSchema = z
  .object({
    origin: z
      .string()
      .length(3, "Must be a 3-letter IATA code")
      .regex(/^[A-Za-z]+$/, "Only letters allowed"),
    destination: z
      .string()
      .length(3, "Must be a 3-letter IATA code")
      .regex(/^[A-Za-z]+$/, "Only letters allowed"),
    departure_date: z.string().min(1, "Departure date is required"),
    return_date: z.string().optional(),
    travelers: z.coerce.number().int().min(1).max(20).default(1),
    trip_type: z.string().default("flight"),
    notes: z.string().max(2000).optional(),
  })
  .refine(
    (data) => {
      if (data.return_date && data.departure_date) {
        return data.return_date > data.departure_date;
      }
      return true;
    },
    {
      message: "Return date must be after departure date",
      path: ["return_date"],
    },
  );

export const priceWatchCreateSchema = z.object({
  trip_id: z.string().min(1, "Trip is required"),
  provider: z.string().default("google_flights"),
  target_price: z.coerce
    .number()
    .positive("Target price must be greater than 0"),
  currency: z.string().length(3).default("USD"),
  alert_cooldown_hours: z.coerce.number().int().min(1).max(168).default(6),
  scrape_interval_minutes: z.coerce
    .number()
    .int()
    .min(15, "Minimum interval is 15 minutes")
    .max(1440, "Maximum interval is 1440 minutes (24 hours)")
    .default(60),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type TripCreateFormData = z.infer<typeof tripCreateSchema>;
export type PriceWatchCreateFormData = z.infer<typeof priceWatchCreateSchema>;

// ──────────────────────────────────────────────────
// API response schemas (runtime validation)
// ──────────────────────────────────────────────────

export const userResponseSchema = z.object({
  id: z.string(),
  email: z.string(),
  full_name: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
});

export const tokenResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
});

export const tripResponseSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  origin: z.string(),
  destination: z.string(),
  departure_date: z.string(),
  return_date: z.string().nullable(),
  travelers: z.number(),
  trip_type: z.string(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const priceWatchResponseSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  trip_id: z.string(),
  provider: z.string(),
  target_price: z.number(),
  currency: z.string(),
  is_active: z.boolean(),
  alert_cooldown_hours: z.number(),
  scrape_interval_minutes: z.number(),
  next_scrape_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const alertResponseSchema = z.object({
  id: z.string(),
  price_watch_id: z.string(),
  user_id: z.string(),
  price_snapshot_id: z.string(),
  alert_type: z.string(),
  channel: z.string(),
  status: z.string(),
  target_price: z.number(),
  triggered_price: z.number(),
  message: z.string().nullable(),
  sent_at: z.string().nullable(),
  created_at: z.string(),
});

export const priceSnapshotResponseSchema = z.object({
  id: z.string(),
  trip_id: z.string(),
  provider: z.string(),
  price: z.number(),
  currency: z.string(),
  cabin_class: z.string().nullable(),
  airline: z.string().nullable(),
  outbound_departure: z.string().nullable(),
  outbound_arrival: z.string().nullable(),
  return_departure: z.string().nullable(),
  return_arrival: z.string().nullable(),
  stops: z.number().nullable(),
  raw_data: z.string().nullable().optional(),
  scraped_at: z.string(),
  created_at: z.string(),
});

// Generic API envelope wrappers
export function apiResponseSchema<T extends z.ZodType>(dataSchema: T) {
  return z.object({
    data: dataSchema.nullable(),
    meta: z.object({ request_id: z.string().optional() }).optional(),
    errors: z.array(z.string()).optional(),
  });
}

export function paginatedResponseSchema<T extends z.ZodType>(dataSchema: T) {
  return z.object({
    data: z.array(dataSchema),
    meta: z.object({
      page: z.number(),
      per_page: z.number(),
      total: z.number(),
      total_pages: z.number(),
    }),
    errors: z.array(z.string()).optional(),
  });
}
