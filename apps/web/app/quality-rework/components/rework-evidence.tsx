import type { QualityReworkResult, ReworkEffort } from "../../../lib/quality-rework";
import { outcomeLabel } from "./format";

export function EffortValues({ effort }: { effort: ReworkEffort }) {
  return <dl className="quality-effort-grid">
    <div><dt>Rework tasks</dt><dd>{effort.tasks}</dd></div>
    <div><dt>Estimated hours</dt><dd>{effort.estimated_hours}</dd></div>
    <div><dt>Completed hours</dt><dd>{effort.completed_hours}</dd></div>
    <div><dt>Remaining hours</dt><dd>{effort.remaining_hours}</dd></div>
  </dl>;
}

export function ReworkOverview({ data }: { data: QualityReworkResult }) {
  const summary = data.quality_summary;
  return <section className="health-section" aria-labelledby="rework-heading">
    <h2 id="rework-heading">Rework Intelligence</h2>
    <dl className="quality-overview">
      <div><dt>Stories with rework</dt><dd>{summary.stories_with_rework}</dd></div>
      <div><dt>Total rework cycles</dt><dd>{summary.total_rework_cycles}</dd></div>
      <div><dt>Completed cycles</dt><dd>{summary.resolved_rework_cycles}</dd></div>
      <div><dt>Active cycles</dt><dd>{summary.active_rework_cycles_at_sprint_end}</dd></div>
      <div><dt>Linked Bugs</dt><dd>{summary.rework_bug_count}</dd></div>
    </dl>
    <p className="section-note">A cycle begins with QA → Returned to DEV. QA acceptance completes a cycle; Bug resolution is separate evidence.</p>
    <ReworkStoryList data={data} />
  </section>;
}

function ReworkStoryList({ data }: { data: QualityReworkResult }) {
  const stories = data.stories.filter((story) => story.rework_cycles > 0);
  return stories.length === 0 ? <p className="page-state">No rework cycles recorded.</p> :
    <ul className="rework-stories">{stories.map((story) => <li key={story.work_item_id}>
      <article aria-label={`Rework ${story.work_item_id}`}>
        <div className="section-heading"><h3>{story.work_item_id}</h3><span className="section-note">Final state: {story.final_state}</span></div>
        <p className="rework-story-meta">First-pass: <strong>{outcomeLabel(story.first_pass_outcome)}</strong> · Rework cycles: {story.rework_cycles}</p>
        <ul className="rework-cycle-list">{data.rework_cycles.filter((cycle) => cycle.work_item_id === story.work_item_id).map((cycle) =>
          <li key={cycle.id} className={cycle.status === "active" ? "quality-active" : undefined}>
            <div className="section-heading"><h4>Cycle {cycle.cycle_number} · {cycle.related_bug_id ?? "No linked Bug"}</h4>
              <span className="quality-cycle-status">{cycle.status === "active" ? "Active rework" : "Completed"}</span></div>
            <p>QA → Returned to DEV <span className="day-date">· Day {cycle.sprint_day}</span></p>
            <p className="event-reference">QA rejection / return to DEV: {cycle.return_to_dev_event_id}
              {cycle.qa_rejection_event_id !== cycle.return_to_dev_event_id && ` · ${cycle.qa_rejection_event_id}`}</p>
            {cycle.bug_detection_event_id && <p className="event-reference">Defect detection: {cycle.bug_detection_event_id}</p>}
            <p className="quiet-note">Bug resolution: {cycle.bug_resolution_status ?? "No linked evidence"}</p>
            {cycle.acceptance_event_id && <p className="event-reference">Rework acceptance: {cycle.acceptance_event_id}</p>}
            {cycle.bug_resolution_event_id && <p className="event-reference">Bug resolution event: {cycle.bug_resolution_event_id}</p>}
          </li>)}</ul>
        <h4>Story rework effort</h4><EffortValues effort={story.rework_effort} />
      </article>
    </li>)}</ul>;
}

export function ReworkEffortSection({ effort }: { effort: ReworkEffort }) {
  return <section className="health-section chart-section" aria-labelledby="effort-heading">
    <h2 id="effort-heading">Rework effort</h2><EffortValues effort={effort} />
    <p className="quiet-note">Rework effort reflects Tasks explicitly classified as rework. It is not a productivity score.</p>
    <p className="quiet-note">Completed hours plus remaining hours may exceed estimated hours. These values are preserved as recorded.</p>
  </section>;
}
