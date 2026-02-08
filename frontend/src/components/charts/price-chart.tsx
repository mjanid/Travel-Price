"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { usePriceHistory } from "@/hooks/use-prices";

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

  const chartData = snapshots
    .slice()
    .sort(
      (a, b) =>
        new Date(a.scraped_at).getTime() - new Date(b.scraped_at).getTime(),
    )
    .map((s) => ({
      date: new Date(s.scraped_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      price: s.price / 100,
      fullDate: s.scraped_at,
    }));

  const targetDollars = targetPrice ? targetPrice / 100 : undefined;

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="#6B7280" />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#6B7280"
            tickFormatter={(v: number) => `$${v}`}
          />
          <Tooltip
            formatter={(value) => [`$${Number(value).toFixed(2)}`, "Price"]}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#2563EB"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
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
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
