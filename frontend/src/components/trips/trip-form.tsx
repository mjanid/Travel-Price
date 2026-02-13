"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateTrip, useUpdateTrip } from "@/hooks/use-trips";
import { tripCreateSchema } from "@/lib/validators";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { AirportSearch } from "@/components/trips/airport-search";
import type { Trip } from "@/lib/types";

interface TripFormProps {
  trip?: Trip;
}

export function TripForm({ trip }: TripFormProps) {
  const router = useRouter();
  const createTrip = useCreateTrip();
  const updateTrip = useUpdateTrip(trip?.id ?? "");
  const isEditing = !!trip;

  const [form, setForm] = useState({
    origin: trip?.origin ?? "",
    destination: trip?.destination ?? "",
    departure_date: trip?.departure_date ?? "",
    return_date: trip?.return_date ?? "",
    travelers: trip?.travelers ?? 1,
    trip_type: trip?.trip_type ?? "flight",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  function handleChange(field: string, value: string | number) {
    setForm({ ...form, [field]: value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const result = tripCreateSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const key = String(issue.path[0]);
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    const payload = { ...result.data, trip_type: form.trip_type };
    const mutation = isEditing ? updateTrip : createTrip;
    mutation.mutate(payload, {
      onSuccess: (res) => {
        if (!res.data) return;
        router.push(`/trips/${res.data.id}`);
      },
      onError: (err: Error) => setErrors({ form: err.message }),
    });
  }

  const isPending = createTrip.isPending || updateTrip.isPending;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errors.form && (
        <p className="rounded-lg bg-red-50 p-3 text-sm text-danger">
          {errors.form}
        </p>
      )}
      <div className="grid gap-4 sm:grid-cols-2">
        <AirportSearch
          label="Origin"
          placeholder="JFK"
          value={form.origin}
          onChange={(code) => handleChange("origin", code)}
          error={errors.origin}
        />
        <AirportSearch
          label="Destination"
          placeholder="LAX"
          value={form.destination}
          onChange={(code) => handleChange("destination", code)}
          error={errors.destination}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Departure date"
          type="date"
          value={form.departure_date}
          onChange={(e) => handleChange("departure_date", e.target.value)}
          error={errors.departure_date}
        />
        <Input
          label="Return date"
          type="date"
          value={form.return_date}
          onChange={(e) => handleChange("return_date", e.target.value)}
          error={errors.return_date}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Number of travelers"
          type="number"
          min={1}
          max={20}
          value={form.travelers}
          onChange={(e) => {
            const parsed = parseInt(e.target.value, 10);
            handleChange("travelers", Number.isNaN(parsed) ? "" : parsed);
          }}
          error={errors.travelers}
        />
        <Select
          label="Trip type"
          value={form.trip_type}
          onChange={(e) => handleChange("trip_type", e.target.value)}
          options={[
            { value: "flight", label: "Flight" },
            { value: "hotel", label: "Hotel" },
            { value: "car_rental", label: "Car Rental" },
          ]}
          error={errors.trip_type}
        />
      </div>
      <div className="flex gap-3">
        <Button type="submit" loading={isPending}>
          {isEditing ? "Update Trip" : "Create Trip"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => router.back()}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
