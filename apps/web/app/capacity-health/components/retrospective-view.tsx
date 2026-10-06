import type { CapacityBreakpoint, CapacityResult } from "../../../lib/capacity-health";
import { CapacityModeNavigation } from "./mode-navigation";
import { SprintProgress } from "./capacity-panels";
import { ReleaseReadiness, SupportIntelligence, Dependencies } from "./context-sections";
import { WhatChanged } from "./what-changed";
import { CapacityEvolution } from "./capacity-evolution";
import { hours, timestamp, words } from "./format";

const BREAKPOINT_LABELS: Record<string, string> = {
  rework: "Rework", post_planning_scope: "Post-planning scope", regression_started: "Regression started",
  regression_completed: "Regression completed", dependency_opened: "Dependency opened", dependency_resolved: "Dependency resolved",
  critical_disruption: "Critical disruption", capacity_gap_crossing: "Capacity gap crossing",
};
export function RetrospectiveHeading() {
  return <div className="health-heading"><p className="eyebrow">v0.2 — Retrospective</p><h1>Capacity Health</h1>
    <p>From Planning to sprint close: outcomes, capacity evolution and the turning points behind them.</p>
    <CapacityModeNavigation mode="retrospective" /></div>;
}
export function RetrospectiveUnavailable() {
  return <div className="sprint-health capacity-health"><RetrospectiveHeading /><section className="page-state" role="alert">
    <h2>Retrospective data is unavailable</h2><p>We couldn’t load the sprint from the API. Please try again.</p>
    <a className="retry-link" href="/capacity-health/retrospective">Try again</a></section></div>;
}
export function SprintTurningPoints({ points }: { points: CapacityBreakpoint[] }) {
  const chronological = [...points].sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  return <section className="health-section capacity-turning-points" aria-labelledby="sprint-turning-points"><h2 id="sprint-turning-points">Sprint turning points</h2>
    <p className="quiet-note">Backend-identified changes from Planning to close. Evidence is preserved without inferring additional causes.</p>
    {points.length === 0 ? <p>No turning points recorded.</p> : <ol className="capacity-evidence">{chronological.map(p =>
      <li key={`${p.timestamp}-${p.kind}-${p.evidence_id ?? p.discipline}`}><h3>{BREAKPOINT_LABELS[p.kind] ?? words(p.kind)}</h3>
        <time dateTime={p.timestamp}>{timestamp(p.timestamp)}</time>
        {p.sprint_day !== undefined ? <span> · Day {p.sprint_day}</span> : null}
        {p.work_item_id ? <p>Work item: <strong>{p.work_item_id}</strong></p> : null}
        {p.discipline ? <p>Discipline: <strong>{p.discipline}</strong></p> : null}
        {p.case_id ? <p>Case: {p.case_id}</p> : null}
        {p.previous_gap_hours !== undefined && p.capacity_gap_hours !== undefined ? <p>Capacity gap: {hours(p.previous_gap_hours)} → {hours(p.capacity_gap_hours)}</p> : null}
        {p.evidence_id ? <small>Evidence: {p.evidence_id}</small> : null}
      </li>)}</ol>}
  </section>;
}
export function RetrospectiveView({ data }: { data: CapacityResult }) {
  const answer = data.mode_context.primary_answer;
  const labels = { yes: "Yes", no: "No", insufficient_data: "Insufficient data" };
  return <div className="sprint-health capacity-health capacity-retrospective"><RetrospectiveHeading />
    <p className="scenario-label">{data.sprint.project} · {data.sprint.backlog} · {data.sprint.name} · Fictional demo data</p>
    <p className="quiet-note">Sprint close · Day {data.mode_context.sprint_day} · {timestamp(data.mode_context.snapshot_at)}</p>
    {data.daily_capacity.length === 0 ? <section className="page-state" role="status"><h2>No retrospective results available</h2></section> : <>
      <section className="capacity-answer capacity-panel" aria-labelledby="final-capacity-outcome"><h2 id="final-capacity-outcome">Final capacity outcome</h2>
        <p>Can we still finish the remaining work with the capacity we have left?</p>
        <p className="capacity-answer-label">{labels[answer.answer]}</p><p>{answer.reason}</p>
        {answer.missing_inputs.length > 0 ? <p className="quiet-note">Missing evidence: {answer.missing_inputs.join(", ")}. Unavailable values are not zero.</p> : null}
      </section>
      <SprintProgress data={data} /><SprintTurningPoints points={data.retrospective_breakpoints} />
      {data.critical_disruptions.length > 0 ? <section className="health-section capacity-panel" aria-labelledby="retro-critical"><h2 id="retro-critical">Critical disruptions during the sprint</h2>
        <ul className="capacity-evidence">{data.critical_disruptions.map(c => <li key={c.case_id}><strong>{c.case_id}</strong> · {c.active ? "Active at close" : "Completed by close"}
          {c.linked_work_item_id ? <p>Affected work: {c.linked_work_item_id}</p> : null}
          {c.events.map(e => <p key={e.id}>{e.description ?? words(e.event_type)} <small>Evidence: {e.id}</small></p>)}</li>)}</ul>
      </section> : null}
      <CapacityEvolution snapshots={data.daily_capacity} />
      <WhatChanged data={data} retrospective /><ReleaseReadiness release={data.release_readiness} />
      <SupportIntelligence data={data} /><Dependencies data={data} />
    </>}
    <aside className="capacity-notes" aria-label="Retrospective principles"><h2>Capacity ≠ Progress</h2>
      <p>Story closure describes delivery progress; hours describe effort and capacity. This fictional team/backlog analysis provides no individual productivity or utilization score, health thresholds or recommendations.</p></aside>
  </div>;
}
