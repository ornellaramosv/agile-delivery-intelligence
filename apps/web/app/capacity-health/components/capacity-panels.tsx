import { CONSUMPTION_LABELS, type CapacityResult } from "../../../lib/capacity-health";
import { hours } from "./format";

export function SprintProgress({ data }: { data: CapacityResult }) {
  return <section className="health-section" aria-labelledby="capacity-progress"><h2 id="capacity-progress">Sprint Progress</h2>
    <div className="capacity-progress-grid">{([
      ["original_baseline", "Original baseline"], ["current_scope", "Current scope"], ["post_planning_scope", "Post-Planning Scope added"],
    ] as const).map(([key, label]) => <article key={key} aria-label={label} className="capacity-panel">
      <h3>{label}</h3><p className="capacity-count">{data.sprint_progress[key].closed} / {data.sprint_progress[key].total} <span>Closed / Total</span></p>
      <p>{data.sprint_progress[key].open} Open</p></article>)}</div>
    <p className="quiet-note">Added scope changes the current scope, not the original commitment. Story closure measures progress; consumed hours do not.</p>
  </section>;
}

export function DisciplineCapacity({ data }: { data: CapacityResult }) {
  return <section className="health-section" aria-labelledby="discipline-capacity"><h2 id="discipline-capacity">DEV and QA capacity</h2>
    <div className="capacity-columns">{(["DEV", "QA"] as const).map(d => {
      const row = data.disciplines[d];
      return <article className="capacity-panel" aria-label={`${d} capacity`} key={d}><h3>{d}</h3>
        <dl className="capacity-metrics"><div className="capacity-gap"><dt>Capacity Gap</dt><dd>{hours(row.capacity.capacity_gap_hours)}</dd></div>
          <div><dt>Remaining delivery demand</dt><dd>{hours(row.remaining_delivery.total_hours)}</dd></div>
          <div><dt>Effective remaining capacity</dt><dd>{hours(row.capacity.effective_remaining_capacity_hours)}</dd></div>
          <div><dt>Actual total consumption</dt><dd>{hours(row.consumption.total_hours)}</dd></div></dl>
        {row.capacity.missing_inputs.length > 0 ? <p className="quiet-note">Missing evidence: {row.capacity.missing_inputs.join(", ")}. Unavailable values are not zero.</p> : null}
      </article>;
    })}</div><p className="quiet-note">Gap is effective remaining capacity minus remaining delivery demand, in hours.</p>
  </section>;
}

export function CapacityConsumption({ data }: { data: CapacityResult }) {
  return <section className="health-section" aria-labelledby="capacity-consumption"><h2 id="capacity-consumption">Capacity Consumption</h2>
    <table className="capacity-table"><caption className="sr-only">Recorded capacity consumption by discipline</caption>
      <thead><tr><th scope="col">Category</th><th scope="col">DEV</th><th scope="col">QA</th></tr></thead>
      <tbody>{Object.entries(CONSUMPTION_LABELS).map(([key, label]) => <tr key={key}><th scope="row">{label}</th>
        {(["DEV", "QA"] as const).map(d => <td key={d}>{hours(data.disciplines[d].consumption[key as keyof typeof CONSUMPTION_LABELS])}</td>)}</tr>)}</tbody>
    </table></section>;
}
