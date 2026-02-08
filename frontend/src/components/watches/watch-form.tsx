"use client";

import { useState } from "react";
import { useCreateWatch } from "@/hooks/use-watches";
import { priceWatchCreateSchema } from "@/lib/validators";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

interface WatchFormProps {
  tripId: string;
  onSuccess?: () => void;
}

export function WatchForm({ tripId, onSuccess }: WatchFormProps) {
  const createWatch = useCreateWatch();
  const [form, setForm] = useState({
    target_price: "",
    provider: "google_flights",
    alert_cooldown_hours: "6",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const result = priceWatchCreateSchema.safeParse({
      trip_id: tripId,
      target_price: form.target_price,
      provider: form.provider,
      alert_cooldown_hours: form.alert_cooldown_hours,
    });

    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const key = String(issue.path[0]);
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    // Convert dollars to cents for the API
    const payload = {
      ...result.data,
      target_price: Math.round(result.data.target_price * 100),
    };

    createWatch.mutate(payload, {
      onSuccess: () => onSuccess?.(),
      onError: (err) => setErrors({ form: err.message }),
    });
  }

  return (
    <Card>
      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.form && (
          <p className="rounded-lg bg-red-50 p-3 text-sm text-danger">
            {errors.form}
          </p>
        )}
        <div className="grid gap-4 sm:grid-cols-3">
          <Input
            label="Target price ($)"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="250.00"
            value={form.target_price}
            onChange={(e) => setForm({ ...form, target_price: e.target.value })}
            error={errors.target_price}
          />
          <Select
            label="Provider"
            value={form.provider}
            onChange={(e) => setForm({ ...form, provider: e.target.value })}
            options={[
              { value: "google_flights", label: "Google Flights" },
              { value: "skyscanner", label: "Skyscanner" },
              { value: "kayak", label: "Kayak" },
            ]}
            error={errors.provider}
          />
          <Input
            label="Cooldown (hours)"
            type="number"
            min="1"
            max="168"
            value={form.alert_cooldown_hours}
            onChange={(e) =>
              setForm({ ...form, alert_cooldown_hours: e.target.value })
            }
            error={errors.alert_cooldown_hours}
          />
        </div>
        <Button type="submit" size="sm" loading={createWatch.isPending}>
          Create Watch
        </Button>
      </form>
    </Card>
  );
}
