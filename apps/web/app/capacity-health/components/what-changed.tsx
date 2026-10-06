import { COMPARISONS, CONSUMPTION_LABELS, type CapacityFact, type CapacityResult } from "../../../lib/capacity-health";
import { hours, timestamp, words } from "./format";

function Evidence({ facts }: { facts: CapacityFact[] }) {
  return <ul className="capacity-evidence">{facts.map(f => <li key={`${f.timestamp}-${f.kind}-${f.evidence_id}`}>
    <strong>{words(f.kind)}</strong>{f.work_item_id ? ` · ${f.work_item_id}` : ""}{f.case_id ? ` · ${f.case_id}` : ""}
    {f.reference_id ? ` · ${f.reference_id}` : ""}{f.task_id ? ` · ${f.task_id}` : ""}
    {f.category ? ` · ${words(f.category)}` : ""}{f.discipline ? ` · ${f.discipline}` : ""}
    {f.hours !== undefined ? ` · ${hours(f.hours)} recorded` : ""}
    {f.remaining_hours !== undefined ? ` · ${hours(f.remaining_hours)} remaining` : ""}
    <small>{timestamp(f.timestamp)} · Evidence: {f.evidence_id}{f.source ? ` · ${f.source}` : ""}</small>
  </li>)}</ul>;
}
export function WhatChanged({ data }: { data: CapacityResult }) {
  const changes = data.what_changed;
  const observations = changes.facts.filter(f => ["effort_recorded", "remaining_delivery_observed"].includes(f.kind));
  const events = changes.facts.filter(f => !["effort_recorded", "remaining_delivery_observed"].includes(f.kind));
  return <section className="health-section" aria-labelledby="what-changed"><h2 id="what-changed">What Changed?</h2>
    <p>{COMPARISONS[changes.comparison]} · {timestamp(changes.from_at)} → {timestamp(changes.to_at)}</p>
    <div className="capacity-columns">{(["DEV", "QA"] as const).map(d => <article className="capacity-panel" key={d} aria-label={`${d} changes`}><h3>{d}</h3>
      <dl className="capacity-metrics"><div><dt>Remaining delivery demand change</dt><dd>{hours(changes.by_discipline[d].remaining_delivery_change_hours, true)}</dd></div>
        <div><dt>Recorded consumption change</dt><dd>{hours(changes.by_discipline[d].consumption_change_hours.total_hours, true)}</dd></div></dl>
      <details><summary>Consumption change by category</summary><dl className="capacity-metrics">{Object.entries(CONSUMPTION_LABELS).map(([key, label]) => <div key={key}>
        <dt>{label}</dt><dd>{hours(changes.by_discipline[d].consumption_change_hours[key as keyof typeof CONSUMPTION_LABELS], true)}</dd></div>)}</dl></details>
    </article>)}</div>
    <p className="quiet-note">Signed changes are supplied by the backend. Evidence explains scope additions, QA returns and non-delivery work; it is not a productivity assessment.</p>
    {events.length > 0 ? <details className="capacity-facts" open><summary>Scope, support, rework and dependency evidence</summary><Evidence facts={events} /></details> : <p>No change events in this comparison window.</p>}
    {observations.length > 0 ? <details className="capacity-facts"><summary>Recorded effort and remaining-work observations</summary><Evidence facts={observations} /></details> : null}
  </section>;
}
