"use client";

import {
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";
import { usePriceHistory } from "@/hooks/use-prices";
import { aggregateSnapshots } from "@/lib/utils";

interface PriceChartProps {
  tripId: string;
  provider?: string;
  targetPrice?: number;
}

export function PriceChart({ tripId, provider, targetPrice }: PriceChartProps) {
  const { data, isLoading, error } = usePriceHistory(tripId, provider);

  if (isLoading) {
    return <p className="text-sm text-muted">Loading price history...</p>;
  }

  if (error) {
    return <p className="text-sm text-danger">Failed to load price data.</p>;
  }

  const snapshots = data?.data ?? [];

  if (snapshots.length === 0) {
    return (
      <p className="text-sm text-muted">
        No price data yet. Prices will appear after scraping runs.
      </p>
    );
  }

  const chartData = aggregateSnapshots(snapshots);
  const targetDollars = targetPrice ? targetPrice / 100 : undefined;

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6B7280" />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#6B7280"
            tickFormatter={(v: number) => `$${v}`}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload;
              return (
                <div className="rounded-lg border border-border bg-white p-3 shadow-md">
                  <p className="text-xs text-muted">{d.date}</p>
                  <p className="font-medium text-primary">
                    Best: ${d.min.toFixed(2)}
                  </p>
                  <p className="text-sm text-muted">
                    Range: ${d.min.toFixed(2)} &ndash; ${d.max.toFixed(2)}
                  </p>
                  <p className="text-xs text-muted">{d.count} results</p>
                </div>
              );
            }}
          />
          <Area
            type="monotone"
            dataKey="max"
            stroke="none"
            fill="#DBEAFE"
            fillOpacity={0.5}
          />
          <Area
            type="monotone"
            dataKey="min"
            stroke="none"
            fill="#FFFFFF"
            fillOpacity={1}
          />
          <Line
            type="monotone"
            dataKey="min"
            stroke="#2563EB"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            name="Best Price"
          />
          {targetDollars && (
            <ReferenceLine
              y={targetDollars}
              stroke="#16A34A"
              strokeDasharray="5 5"
              label={{
                value: `Target: $${targetDollars}`,
                position: "right",
                fill: "#16A34A",
                fontSize: 12,
              }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
