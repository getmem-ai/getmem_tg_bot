"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { BarChart3 } from "lucide-react";
import type { UsagePoint } from "@/lib/types";
import { shortDay } from "@/lib/format";
import { Card, SectionTitle } from "./Card";

interface UsageChartProps {
  series: UsagePoint[];
}

interface TooltipPayloadItem {
  value: number;
  payload: UsagePoint;
}

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-lg border border-black/10 bg-tg-bg px-2.5 py-1.5 text-xs shadow-sm">
      <div className="font-medium text-tg-text">{shortDay(point.day)}</div>
      <div className="text-tg-hint">{point.count} messages</div>
    </div>
  );
}

export function UsageChart({ series }: UsageChartProps) {
  const data = series.map((p) => ({ ...p, label: shortDay(p.day) }));
  const total = series.reduce((sum, p) => sum + p.count, 0);

  return (
    <Card>
      <SectionTitle
        icon={BarChart3}
        right={<span className="text-xs text-tg-hint">{total} total</span>}
      >
        Last {series.length} days
      </SectionTitle>

      {total === 0 ? (
        <div className="flex h-40 items-center justify-center text-sm text-tg-hint">
          No activity yet
        </div>
      ) : (
        <div className="h-40 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 6, right: 6, left: -22, bottom: 0 }}
            >
              <defs>
                <linearGradient id="usageFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--tg-button)" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="var(--tg-button)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--tg-hint)"
                strokeOpacity={0.12}
                vertical={false}
              />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 10, fill: "var(--tg-hint)" }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                minTickGap={16}
              />
              <YAxis
                allowDecimals={false}
                width={28}
                tick={{ fontSize: 10, fill: "var(--tg-hint)" }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                content={<ChartTooltip />}
                cursor={{ stroke: "var(--tg-hint)", strokeOpacity: 0.2 }}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="var(--tg-button)"
                strokeWidth={2}
                fill="url(#usageFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
