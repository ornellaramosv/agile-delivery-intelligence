import type { QualityReworkResult } from "../../../lib/quality-rework";
import { formatRate, outcomeLabel } from "./format";

export function FirstPassQA({ data }: { data: QualityReworkResult }) {
  const summary = data.quality_summary;
  return <section className="health-section chart-section" aria-labelledby="first-pass-heading">
    <h2 id="first-pass-heading">First-pass QA</h2>
    <p className="section-note">First-pass QA measures whether eligible User Stories passed QA without returning to Development for defect correction.</p>
    <div className="qa-ratio"><strong>{summary.first_pass_successes} passed / {summary.eligible_qa_stories} eligible</strong>
      <span>{formatRate(summary.first_pass_qa_rate)}</span></div>
    {summary.first_pass_qa_rate !== null && <meter className="qa-meter" min={0} max={1}
      value={summary.first_pass_qa_rate} aria-label="First-pass QA rate">{formatRate(summary.first_pass_qa_rate)}</meter>}
    <p className="quiet-note">Stories that did not reach QA are not in the denominator. Client-incident scope-added work is excluded from this v0.1 metric. Eligible roadmap carry-over is included.</p>
    <h3 className="qa-population-heading">Population detail</h3>
    <p className="quiet-note">All active-scope stories and their first-pass classification.</p>
    <ul className="qa-population">{data.stories.map((story) => <li key={story.work_item_id}>
      <article aria-label={`QA ${story.work_item_id}`}>
        <div className="qa-story-title"><strong>{story.work_item_id}</strong><span className={`qa-outcome qa-${story.first_pass_outcome ?? "unknown"}`}>{outcomeLabel(story.first_pass_outcome)}</span></div>
        <p className="quiet-note">{story.first_pass_population ? "Eligible" : "Outside denominator"}{story.carry_over ? " · Carry-over" : ""}</p>
        {story.first_pass_outcome === "not_reached_qa" && <p className="quiet-note">No QA attempt in this sprint.</p>}
        {story.outcome_reason === "client_incident_excluded_in_v0.1" && <p className="quiet-note">Client incident · excluded under the v0.1 population rule.</p>}
        {story.first_pass_outcome === null && <p className="quiet-note">No first-attempt outcome recorded.</p>}
      </article>
    </li>)}</ul>
  </section>;
}
