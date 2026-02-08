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
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
export type TripCreateFormData = z.infer<typeof tripCreateSchema>;
export type PriceWatchCreateFormData = z.infer<typeof priceWatchCreateSchema>;
