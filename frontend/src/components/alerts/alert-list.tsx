"use client";

import { useState } from "react";
import { useAlerts } from "@/hooks/use-alerts";
import { useWatchAlerts } from "@/hooks/use-alerts";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatPrice, formatDate } from "@/lib/utils";
import { AlertSkeleton } from "@/components/ui/skeleton";
import type { Alert } from "@/lib/types";

function AlertRow({ alert }: { alert: Alert }) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Badge
              variant={alert.status === "sent" ? "success" : "danger"}
            >
              {alert.status}
            </Badge>
            <span className="text-xs text-muted">{alert.channel}</span>
          </div>
          <p className="mt-2 text-sm text-foreground">
            Price dropped to{" "}
            <span className="font-semibold text-success">
              {formatPrice(alert.triggered_price)}
            </span>{" "}
            (target: {formatPrice(alert.target_price)})
          </p>
          {alert.message && (
            <p className="mt-1 text-xs text-muted">{alert.message}</p>
          )}
        </div>
        <span className="text-xs text-muted">
          {alert.sent_at ? formatDate(alert.sent_at) : "Pending"}
        </span>
      </div>
    </Card>
  );
}

interface AlertListProps {
  watchId?: string;
}

export function AlertList({ watchId }: AlertListProps) {
  const [page, setPage] = useState(1);
  const allAlerts = useAlerts(page, 10);
  const watchAlertQuery = useWatchAlerts(watchId ?? "", page, 10);

  const query = watchId ? watchAlertQuery : allAlerts;
  const { data, isLoading, error } = query;

  const alerts = data?.data ?? [];
  const meta = data?.meta;

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <AlertSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return <p className="text-sm text-danger">Failed to load alerts.</p>;
  }

  if (alerts.length === 0) {
    return (
      <p className="text-sm text-muted">
        No alerts yet. Alerts are sent when prices drop below your target.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {alerts.map((alert) => (
          <AlertRow key={alert.id} alert={alert} />
        ))}
      </div>

      {meta && meta.total_pages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted">
            Page {meta.page} of {meta.total_pages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= meta.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
