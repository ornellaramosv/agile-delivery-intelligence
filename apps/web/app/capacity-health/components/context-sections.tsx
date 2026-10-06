import type { CapacityResult } from "../../../lib/capacity-health";
import { hours, words } from "./format";

export function ReleaseReadiness({ release }: { release: CapacityResult["release_readiness"] }) {
  if (release.status !== "applicable") return null;
  const s = release.summary;
  return <section className="health-section capacity-panel" aria-labelledby="release-readiness"><h2 id="release-readiness">Release Readiness</h2>
    <p><strong>{release.release_id}</strong> · Ready for Regression: <strong>{release.ready_for_regression ? "Yes" : "No"}</strong></p>
    <dl className="capacity-metrics">
      <div><dt>Total release scope</dt><dd>{s.closed_scope_items} / {s.total_scope_items} Closed / Total · {s.pending_scope_items} Pending</dd></div>
      <div><dt>Current-sprint release-required US</dt><dd>{s.current_sprint_required_closed} / {s.current_sprint_required_total} Closed / Total · {s.current_sprint_required_pending} Pending</dd></div>
      <div><dt>Included customer / BOC engineering cases</dt><dd>{s.included_customer_cases_engineering_closed} / {s.included_customer_cases_total} Closed / Total · {s.included_customer_cases_pending} Pending</dd></div>
      <div><dt>Regression phase</dt><dd>{words(release.regression_phase)}</dd></div>
    </dl>
    <p>Required for this release: {release.current_sprint_required_ids.join(", ") || "None"}.</p>
    <p>Targeting future releases: {release.current_sprint_future_release_ids.join(", ") || "None"}.</p>
    <p className="quiet-note">Release scope can span sprints. Readiness uses story closure and engineering case closure; DevOps, pipeline and environment dependencies are context, not readiness gates.</p>
  </section>;
}

export function SupportIntelligence({ data }: { data: CapacityResult }) {
  return <section className="health-section" aria-labelledby="support-intelligence"><h2 id="support-intelligence">Support Intelligence</h2>
    <p className="quiet-note">Standard support evidence. Critical incidents are excluded from this historical trend.</p>
    <div className="capacity-columns">
      <section className="capacity-panel" aria-labelledby="support-planning"><h3 id="support-planning">Forecast / Reserve / Actual</h3>
        <table className="capacity-table"><caption className="sr-only">Standard support hours</caption><thead><tr><th scope="col">Hours</th><th scope="col">DEV</th><th scope="col">QA</th></tr></thead>
          <tbody>{([["forecast_hours", "Forecast"], ["reserved_hours", "Reserved"], ["actual_hours", "Actual"]] as const).map(([key, label]) => <tr key={key}>
            <th scope="row">{label}</th>{(["DEV", "QA"] as const).map(d => <td key={d}>{hours(data.disciplines[d].support[key])}</td>)}</tr>)}</tbody></table>
        {(["DEV", "QA"] as const).map(d => <p className="quiet-note" key={d}>{d} forecast: {words(data.disciplines[d].support.forecast_status)}.</p>)}
      </section>
      <section className="capacity-panel" aria-labelledby="support-history"><h3 id="support-history">Historical support trend</h3>
        {data.support.history.length === 0 ? <p>No historical support evidence available.</p> : <ol className="capacity-history">
          {data.support.history.map(period => <li key={period.sprint_id}><strong>{period.sprint_id}</strong> · {period.standard_case_count} standard cases
            <dl className="capacity-inline-metrics">{Object.entries(period.actual_hours).map(([d, value]) => <div key={d}><dt>{d}</dt><dd>{hours(value)}</dd></div>)}</dl>
          </li>)}</ol>}
      </section>
    </div></section>;
}

export function Dependencies({ data }: { data: CapacityResult }) {
  return <section className="health-section" aria-labelledby="capacity-dependencies"><h2 id="capacity-dependencies">Dependencies</h2>
    <p className="quiet-note">Elapsed calendar time is not team effort or lost capacity. Durations include nights and weekends.</p>
    {data.dependencies.items.length === 0 ? <p>No dependencies recorded for this snapshot.</p> : <ul className="capacity-evidence">
      {data.dependencies.items.map(dep => <li key={dep.id}><h3>{dep.work_item_ids.join(", ")}</h3>
        <p>{words(dep.type)} · {dep.owner} · {dep.resolved_at ? "Resolved" : "Open"}</p>
        <p><strong>Elapsed open duration: {hours(dep.elapsed_open_hours)}</strong></p>
        <p className="quiet-note">Actual technical effort: {hours(dep.technical_actual_hours)} · {dep.id} · {dep.time_entry_ids.join(", ")}</p>
      </li>)}</ul>}
  </section>;
}
