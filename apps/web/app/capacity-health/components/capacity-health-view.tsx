import { COMPARISONS, SPRINT_DAYS, capacityQuery, type CapacityResult, type CapacitySelection } from "../../../lib/capacity-health";
import { CapacityConsumption, DisciplineCapacity, SprintProgress } from "./capacity-panels";
import { Dependencies, ReleaseReadiness, SupportIntelligence } from "./context-sections";
import { WhatChanged } from "./what-changed";
import { CapacityModeNavigation } from "./mode-navigation";
import { timestamp } from "./format";

export function CapacityHeading() {
  return <div className="health-heading"><p className="eyebrow">v0.2 — Current Sprint</p><h1>Capacity Health</h1>
    <p>Remaining delivery demand, available capacity and the evidence behind changes.</p><CapacityModeNavigation mode="current_sprint" /></div>;
}
export function CapacitySelectors({ selection }: { selection: CapacitySelection }) {
  return <form action="/capacity-health" method="get" className="capacity-selectors" aria-label="Current Sprint snapshot">
    <label htmlFor="capacity-day">Sprint day<select id="capacity-day" name="sprint_day" defaultValue={selection.sprint_day}>
      {SPRINT_DAYS.map(day => <option value={day} key={day}>Day {day}</option>)}</select></label>
    <label htmlFor="capacity-comparison">What Changed comparison<select id="capacity-comparison" name="comparison" defaultValue={selection.comparison}>
      {Object.entries(COMPARISONS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
    <button type="submit">Apply snapshot</button>
  </form>;
}
export function CapacityUnavailable({ selection }: { selection: CapacitySelection }) {
  return <div className="sprint-health capacity-health"><CapacityHeading /><CapacitySelectors selection={selection} />
    <section className="page-state" role="alert"><h2>Capacity data is unavailable</h2>
      <p>We couldn’t load the sprint from the API. Check that the ADI API is running, then try again.</p>
      <a className="retry-link" href={`/capacity-health?${capacityQuery(selection)}`}>Try again</a></section></div>;
}
export function CapacityHealthView({ data }: { data: CapacityResult }) {
  const answer = data.mode_context.primary_answer;
  const labels = { yes: "Yes", no: "No", insufficient_data: "Insufficient data" };
  const activeCritical = data.critical_disruptions.filter(c => c.active);
  return <div className="sprint-health capacity-health"><CapacityHeading />
    <p className="scenario-label">{data.sprint.project} · {data.sprint.backlog} · {data.sprint.name} · Fictional demo data</p>
    <CapacitySelectors selection={data.mode_context} />
    <p className="quiet-note">Current Sprint · Day {data.mode_context.sprint_day} · End-of-day snapshot: {timestamp(data.mode_context.snapshot_at)}</p>
    {data.daily_capacity.length === 0 ? <section className="page-state" role="status"><h2>No capacity results available</h2><p>No snapshots are available for this sprint.</p></section> : <>
      {activeCritical.length > 0 ? <section className="capacity-critical" aria-labelledby="critical-disruption"><h2 id="critical-disruption">Critical disruption active</h2>
        <ul>{activeCritical.map(c => <li key={c.case_id}><strong>{c.case_id}</strong>{c.linked_work_item_id ? ` · Affected work: ${c.linked_work_item_id}` : " · Engineering case"}
          {c.events.filter(e => e.description).map(e => <p key={e.id}>{e.description}</p>)}</li>)}</ul>
      </section> : null}
      <section className="capacity-answer capacity-panel" aria-labelledby="capacity-question">
        <h2 id="capacity-question">Can we still finish the remaining work with the capacity we have left?</h2>
        <p className="capacity-answer-label">{labels[answer.answer]}</p><p>{answer.reason}</p>
        {answer.missing_inputs.length > 0 ? <p className="quiet-note">Missing evidence: {answer.missing_inputs.join(", ")}. Insufficient data describes evidence availability, not a health state.</p> : null}
      </section>
      <SprintProgress data={data} /><DisciplineCapacity data={data} /><CapacityConsumption data={data} />
      <WhatChanged data={data} /><ReleaseReadiness release={data.release_readiness} />
      <SupportIntelligence data={data} /><Dependencies data={data} />
    </>}
    <aside className="capacity-notes" aria-label="Capacity Health principles"><h2>Capacity ≠ Progress</h2>
      <p>Hours describe effort and capacity. Closed User Stories describe delivery progress. This fictional demo analyzes the team and backlog, not individual productivity. It provides no utilization score or recommendations.</p>
    </aside>
  </div>;
}
