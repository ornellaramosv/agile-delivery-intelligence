"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { FlowSnapshot } from "../../../lib/delivery-flow";
import { flowColor } from "./flow-colors";

export function FlowTimelineChart({ snapshots, states }: { snapshots: FlowSnapshot[]; states: string[] }) {
  return <section className="health-section chart-section" aria-labelledby="flow-timeline-heading">
    <h2 id="flow-timeline-heading">Flow across sprint</h2>
    <p className="section-note">End-of-day User Story composition · Each bar represents active scope</p>
    <ul className="chart-legend flow-legend" aria-label="Workflow state legend">
      {states.map((state, index) => <li key={state}><span className="flow-swatch" style={{ background: flowColor(index) }} />{state}</li>)}
    </ul>
    <div className="chart-frame" role="group" aria-label="Workflow composition by sprint day" aria-describedby="flow-chart-caption">
      <ResponsiveContainer width="100%" height="100%" minWidth={0} initialDimension={{ width: 800, height: 300 }}>
        <BarChart data={snapshots} margin={{ top: 12, right: 0, bottom: 8, left: -25 }} accessibilityLayer>
          <CartesianGrid vertical={false} stroke="#e4e9ed" />
          <XAxis dataKey="sprint_day" tickFormatter={(day) => `D${day}`} interval={0} tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
          <Tooltip labelFormatter={(day) => `Day ${day}`} isAnimationActive={false} />
          {states.map((state, index) => <Bar key={state} dataKey={(snapshot: FlowSnapshot) => snapshot.states[state]}
            name={state} stackId="flow" fill={flowColor(index)} isAnimationActive={false} />)}
        </BarChart>
      </ResponsiveContainer>
    </div>
    <p className="chart-caption" id="flow-chart-caption">Daily snapshots, not cumulative totals. State colors identify workflow positions, not delivery health.</p>
    <details className="flow-data-table"><summary>View daily snapshot values</summary>
      <div className="flow-table-scroll" tabIndex={0} role="region" aria-label="Daily snapshot values">
        <table><caption>API workflow counts and active scope</caption><thead><tr><th scope="col">Day</th>
          {states.map((state) => <th scope="col" key={state}>{state}</th>)}<th scope="col">Active scope</th></tr></thead>
          <tbody>{snapshots.map((snapshot) => <tr key={snapshot.sprint_day}><th scope="row">{snapshot.sprint_day}</th>
            {states.map((state) => <td key={state}>{snapshot.states[state]}</td>)}<td>{snapshot.total_active_scope}</td></tr>)}</tbody>
        </table>
      </div>
    </details>
  </section>;
}
