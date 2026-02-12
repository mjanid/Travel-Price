"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateTrip, useUpdateTrip } from "@/hooks/use-trips";
import { tripCreateSchema } from "@/lib/validators";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

    const mutation = isEditing ? updateTrip : createTrip;
    mutation.mutate(result.data, {
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
        <Input
          label="Origin (IATA code)"
          placeholder="JFK"
          value={form.origin}
          onChange={(e) => handleChange("origin", e.target.value.toUpperCase())}
          error={errors.origin}
          maxLength={3}
        />
        <Input
          label="Destination (IATA code)"
          placeholder="LAX"
          value={form.destination}
          onChange={(e) =>
            handleChange("destination", e.target.value.toUpperCase())
          }
          error={errors.destination}
          maxLength={3}
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
      <Input
        label="Number of travelers"
        type="number"
        min={1}
        max={20}
        value={form.travelers}
        onChange={(e) => handleChange("travelers", parseInt(e.target.value, 10))}
        error={errors.travelers}
      />
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
