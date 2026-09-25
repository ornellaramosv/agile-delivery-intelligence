import type { BurndownResult } from "../../../lib/burndown";
import { dateLabel } from "./format";

export function SprintSummary({ data }: { data: BurndownResult }) {
  const first = data.daily_snapshots[0];
  const latest = data.daily_snapshots.at(-1);
  return (
    <section className="sprint-summary" aria-labelledby="sprint-summary-heading">
      <div className="section-heading">
        <h2 id="sprint-summary-heading">Sprint summary</h2>
        <span className="scenario-label">Fictional demo scenario</span>
      </div>
      <dl className="summary-grid">
        <div><dt>Project</dt><dd>{data.sprint.project}</dd></div>
        <div><dt>Backlog</dt><dd>{data.sprint.backlog}</dd></div>
        <div><dt>Sprint</dt><dd>{data.sprint.name}</dd></div>
        <div><dt>Scenario duration</dt><dd>{data.daily_snapshots.length ? `${data.daily_snapshots.length} working days` : "Unavailable"}</dd></div>
        <div><dt>Original baseline</dt><dd>{first ? <><strong>{first.original_baseline}</strong> User Stories</> : "Unavailable"}</dd></div>
        <div><dt>{latest ? `Remaining at Day ${latest.sprint_day}` : "Current remaining work"}</dt><dd>{latest ? <><strong>{latest.current_remaining_work}</strong> delivery work items</> : "Unavailable"}</dd></div>
      </dl>
      <p className="section-note">{dateLabel(data.sprint.start_date)} – {dateLabel(data.sprint.end_date)} · End-of-day snapshots · {data.sprint.timezone}</p>
    </section>
  );
}
