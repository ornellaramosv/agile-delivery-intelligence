"use client";

import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailySnapshot } from "../../../lib/burndown";

export function BurndownChart({ snapshots }: { snapshots: DailySnapshot[] }) {
  const baseline = snapshots[0]?.original_baseline;
  return (
    <section className="health-section chart-section" aria-labelledby="burndown-heading">
      <div className="section-heading">
        <div>
          <h2 id="burndown-heading">Burndown Intelligence</h2>
          <p className="section-note">Remaining delivery work items</p>
        </div>
        <ul className="chart-legend" aria-label="Chart legend">
          <li><span className="legend-line actual-line" />Actual Remaining Work</li>
          <li><span className="legend-line baseline-line" />Original Baseline: {baseline}</li>
        </ul>
      </div>
      <div className="chart-frame" role="group" aria-label="Actual remaining work by sprint day" aria-describedby="chart-description">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} initialDimension={{ width: 800, height: 300 }}>
          <LineChart data={snapshots} margin={{ top: 24, right: 20, bottom: 12, left: -20 }} accessibilityLayer>
            <CartesianGrid stroke="#e4e9ed" vertical={false} />
            <XAxis dataKey="sprint_day" tickFormatter={(day) => `D${day}`} interval={0} tickLine={false} axisLine={false} tick={{ fill: "#526474", fontSize: 12 }} />
            <YAxis domain={[0, "auto"]} allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "#526474", fontSize: 12 }} />
            <Tooltip labelFormatter={(day) => `Day ${day}`} formatter={(value) => [value, "Actual Remaining Work"]} isAnimationActive={false} />
            <ReferenceLine y={baseline} stroke="#7f8c98" strokeDasharray="5 5" ifOverflow="extendDomain" />
            <Line type="linear" dataKey="current_remaining_work" name="Actual Remaining Work" stroke="#245e78" strokeWidth={3} dot={{ r: 4, fill: "#fff", strokeWidth: 2 }} activeDot={{ r: 6 }} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p id="chart-description" className="chart-caption">Original Baseline is a fixed reference, not an expected trajectory. Daily values, movements, and causal activity are listed below.</p>
    </section>
  );
}
