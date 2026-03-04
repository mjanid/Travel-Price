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

const INTERVAL_OPTIONS = [
  { value: "15", label: "15 min" },
  { value: "30", label: "30 min" },
  { value: "60", label: "1 hour" },
  { value: "120", label: "2 hours" },
  { value: "240", label: "4 hours" },
  { value: "480", label: "8 hours" },
  { value: "720", label: "12 hours" },
  { value: "1440", label: "24 hours" },
];

export function WatchForm({ tripId, onSuccess }: WatchFormProps) {
  const createWatch = useCreateWatch();
  const [form, setForm] = useState({
    target_price: "",
    provider: "google_flights",
    alert_cooldown_hours: "6",
    scrape_interval_minutes: "60",
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
      scrape_interval_minutes: form.scrape_interval_minutes,
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

    // Convert dollars to cents for the API using string split to avoid
    // floating-point precision issues (e.g. 249.995 * 100 !== 24999.5)
    const priceStr = String(result.data.target_price);
    const [whole = "0", frac = ""] = priceStr.split(".");
    const cents = parseInt(whole, 10) * 100 + parseInt((frac + "00").slice(0, 2), 10);

    const payload = {
      ...result.data,
      target_price: cents,
    };

    createWatch.mutate(payload, {
      onSuccess: () => onSuccess?.(),
      onError: (err: Error) => setErrors({ form: err.message }),
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
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
          <Select
            label="Check interval"
            value={form.scrape_interval_minutes}
            onChange={(e) =>
              setForm({ ...form, scrape_interval_minutes: e.target.value })
            }
            options={INTERVAL_OPTIONS}
            error={errors.scrape_interval_minutes}
          />
        </div>
        <Button type="submit" size="sm" loading={createWatch.isPending}>
          Create Watch
        </Button>
      </form>
    </Card>
  );
}
