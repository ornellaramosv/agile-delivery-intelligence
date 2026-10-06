"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DailyCapacity } from "../../../lib/capacity-health";
import { hours } from "./format";

export function CapacityEvolution({ snapshots }: { snapshots: DailyCapacity[] }) {
  return <section className="health-section" aria-labelledby="capacity-evolution"><h2 id="capacity-evolution">Capacity evolution</h2>
    <p className="quiet-note">End-of-day hours from the backend. Gaps in a line mean unavailable evidence, not zero.</p>
    <div className="capacity-columns">{(["DEV", "QA"] as const).map(d => {
      // Projection for chart rendering only: no arithmetic or inferred values.
      const rows = snapshots.map(s => ({ day: s.sprint_day, demand: s.disciplines[d].remaining_delivery.total_hours,
        effective: s.disciplines[d].capacity.effective_remaining_capacity_hours, gap: s.disciplines[d].capacity.capacity_gap_hours }));
      return <article className="capacity-panel" key={d} aria-label={`${d} evolution`}><h3>{d}</h3>
        <ul className="capacity-evolution-legend" aria-label={`${d} line legend`}>
          <li>Solid blue: Remaining delivery demand</li><li>Dashed gray: Effective remaining capacity</li><li>Dotted purple: Capacity gap</li>
        </ul>
        <div className="capacity-evolution-chart" role="group" aria-label={`${d} daily capacity chart`}>
          <ResponsiveContainer width="100%" height="100%" minWidth={0} initialDimension={{ width: 380, height: 260 }}>
            <LineChart data={rows} accessibilityLayer margin={{ top: 12, right: 8, bottom: 8, left: -20 }}>
              <CartesianGrid vertical={false} stroke="#e4e9ed" />
              <XAxis dataKey="day" tickFormatter={day => `D${day}`} tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} unit=" h" />
              <Tooltip labelFormatter={day => `Day ${day}`} isAnimationActive={false} />
              <Line dataKey="demand" name="Remaining delivery demand (h)" stroke="#245e78" strokeWidth={2} dot={false} isAnimationActive={false} connectNulls={false} />
              <Line dataKey="effective" name="Effective remaining capacity (h)" stroke="#667584" strokeWidth={2} strokeDasharray="6 4" dot={false} isAnimationActive={false} connectNulls={false} />
              <Line dataKey="gap" name="Capacity gap (h)" stroke="#695783" strokeWidth={2} strokeDasharray="2 3" dot={false} isAnimationActive={false} connectNulls={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <details><summary>{d} daily values</summary><table className="capacity-table capacity-evolution-table"><caption>{d} daily capacity hours</caption>
          <thead><tr><th scope="col">Day</th><th scope="col">Demand</th><th scope="col">Effective capacity</th><th scope="col">Gap</th></tr></thead>
          <tbody>{rows.map(row => <tr key={row.day}><th scope="row">{row.day}</th><td>{hours(row.demand)}</td><td>{hours(row.effective)}</td><td>{hours(row.gap)}</td></tr>)}</tbody>
        </table></details>
      </article>;
    })}</div><p className="quiet-note">Line styles distinguish measures, not health levels. DEV and QA use separate hour axes.</p>
  </section>;
}
