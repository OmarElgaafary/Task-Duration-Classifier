import * as React from "react";
import { ResponsiveContainer } from "recharts";
import { cn } from "@/lib/utils";

type ChartConfig = Record<string, { label: string; color: string }>;

function ChartContainer({
  config,
  className,
  children
}: React.HTMLAttributes<HTMLDivElement> & {
  config: ChartConfig;
  children: React.ReactElement;
}) {
  const style = Object.entries(config).reduce<Record<string, string>>(
    (acc, [key, item]) => {
      acc[`--color-${key}`] = item.color;
      return acc;
    },
    {}
  );

  return (
    <div className={cn("h-[280px] w-full", className)} style={style}>
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}

function ChartTooltipContent({
  active,
  payload,
  label,
  formatter
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; color?: string }>;
  label?: string;
  formatter?: (value: number) => string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-md border bg-background px-3 py-2 text-sm shadow-md">
      {label ? <div className="mb-1 font-medium">{label}</div> : null}
      {payload.map((item) => (
        <div key={item.name} className="flex items-center gap-2 text-muted-foreground">
          <span
            className="h-2.5 w-2.5 rounded-sm"
            style={{ backgroundColor: item.color }}
          />
          <span>{item.name}</span>
          <span className="ml-auto tabular-nums text-foreground">
            {formatter && typeof item.value === "number"
              ? formatter(item.value)
              : item.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export { ChartContainer, ChartTooltipContent, type ChartConfig };
