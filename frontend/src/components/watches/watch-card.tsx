"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useUpdateWatch, useDeleteWatch } from "@/hooks/use-watches";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { formatPrice } from "@/lib/utils";
import type { PriceWatch } from "@/lib/types";

interface WatchCardProps {
  watch: PriceWatch;
}

function formatInterval(minutes: number): string {
  if (minutes < 60) return `${minutes}min`;
  const hours = minutes / 60;
  if (Number.isInteger(hours)) return `${hours}h`;
  return `${minutes}min`;
}

function formatNextScrape(iso: string | null): string {
  if (!iso) return "Pending";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  if (diffMs <= 0) return "Due now";
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 60) return `in ${diffMin}min`;
  const diffHours = Math.round(diffMin / 60);
  return `in ${diffHours}h`;
}

export function WatchCard({ watch }: WatchCardProps) {
  const router = useRouter();
  const updateWatch = useUpdateWatch(watch.id);
  const deleteWatch = useDeleteWatch();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  function handleToggle() {
    updateWatch.mutate({ is_active: !watch.is_active });
  }

  function handleDeleteConfirm() {
    deleteWatch.mutate(watch.id, {
      onSuccess: () => setShowDeleteConfirm(false),
    });
  }

  return (
    <>
      <Card>
        <div className="flex items-start justify-between">
          <div
            className="cursor-pointer"
            onClick={() => router.push(`/watches/${watch.id}`)}
          >
            <p className="font-semibold text-foreground">{watch.provider}</p>
            <p className="mt-1 text-sm text-muted">
              Target: {formatPrice(watch.target_price, watch.currency)}
            </p>
            <p className="mt-1 text-xs text-muted">
              Cooldown: {watch.alert_cooldown_hours}h &middot; Every{" "}
              {formatInterval(watch.scrape_interval_minutes)}
            </p>
            <p className="mt-1 text-xs text-muted">
              Next check: {formatNextScrape(watch.next_scrape_at)}
            </p>
          </div>
          <Badge variant={watch.is_active ? "success" : "default"}>
            {watch.is_active ? "Active" : "Paused"}
          </Badge>
        </div>
        <div className="mt-3 flex gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={handleToggle}
            loading={updateWatch.isPending}
          >
            {watch.is_active ? "Pause" : "Resume"}
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => setShowDeleteConfirm(true)}
            loading={deleteWatch.isPending}
          >
            Delete
          </Button>
        </div>
      </Card>

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Delete Price Watch"
        message="Are you sure you want to delete this price watch? You will no longer receive alerts for this target price."
        confirmText="Delete"
        variant="danger"
        loading={deleteWatch.isPending}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </>
  );
}
