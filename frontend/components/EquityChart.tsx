"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

interface EquityChartProps {
  equityCurve: number[];
  times: string[];
}

export default function EquityChart({ equityCurve, times }: EquityChartProps) {
  const data = equityCurve.map((val, i) => ({
    time: times[i]?.split("T")[0] || i,
    equity: Number(val.toFixed(2)),
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 12 }} />
          <YAxis stroke="#64748b" tick={{ fontSize: 12 }} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }}
            labelStyle={{ color: "#cbd5e1" }}
          />
          <Line type="monotone" dataKey="equity" stroke="#38bdf8" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
