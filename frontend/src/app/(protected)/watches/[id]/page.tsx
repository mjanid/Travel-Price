"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { useWatch, useUpdateWatch, useDeleteWatch } from "@/hooks/use-watches";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PriceChart } from "@/components/charts/price-chart";
import { AlertList } from "@/components/alerts/alert-list";
import { formatPrice, formatDate } from "@/lib/utils";

export default function WatchDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data, isLoading, error } = useWatch(id);
  const updateWatch = useUpdateWatch(id);
  const deleteWatch = useDeleteWatch();

  if (isLoading) {
    return <p className="text-sm text-muted">Loading watch...</p>;
  }

  if (error || !data) {
    return (
      <p className="text-sm text-danger">
        Failed to load watch: {error?.message ?? "Not found"}
      </p>
    );
  }

  const watch = data.data!;

  function handleToggle() {
    updateWatch.mutate({ is_active: !watch.is_active });
  }

  function handleDelete() {
    if (!confirm("Delete this price watch?")) return;
    deleteWatch.mutate(id, {
      onSuccess: () => router.push("/watches"),
    });
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">
          {watch.provider}
        </h1>
        <Badge variant={watch.is_active ? "success" : "default"}>
          {watch.is_active ? "Active" : "Paused"}
        </Badge>
      </div>

      <Card>
        <dl className="grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-muted">Target Price</dt>
            <dd className="font-medium text-foreground">
              {formatPrice(watch.target_price, watch.currency)}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Currency</dt>
            <dd className="font-medium text-foreground">{watch.currency}</dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Alert Cooldown</dt>
            <dd className="font-medium text-foreground">
              {watch.alert_cooldown_hours} hours
            </dd>
          </div>
          <div>
            <dt className="text-sm text-muted">Created</dt>
            <dd className="font-medium text-foreground">
              {formatDate(watch.created_at)}
            </dd>
          </div>
        </dl>
      </Card>

      <div className="flex gap-3">
        <Button
          variant="secondary"
          onClick={handleToggle}
          loading={updateWatch.isPending}
        >
          {watch.is_active ? "Pause" : "Resume"}
        </Button>
        <Button
          variant="danger"
          onClick={handleDelete}
          loading={deleteWatch.isPending}
        >
          Delete
        </Button>
        <Button variant="secondary" onClick={() => router.back()}>
          Back
        </Button>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">
          Price History
        </h2>
        <Card>
          <PriceChart
            tripId={watch.trip_id}
            provider={watch.provider}
            targetPrice={watch.target_price}
          />
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-foreground">
          Alert History
        </h2>
        <AlertList watchId={id} />
      </div>
    </div>
  );
}
