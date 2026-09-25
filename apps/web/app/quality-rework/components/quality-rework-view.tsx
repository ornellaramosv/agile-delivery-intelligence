import type { QualityReworkResult } from "../../../lib/quality-rework";
import { FirstPassQA } from "./first-pass-qa";
import { ReworkOverview, ReworkEffortSection } from "./rework-evidence";
import { formatRate } from "./format";

export function QualityHeading() {
  return <div className="health-heading"><p className="eyebrow">Sprint Intelligence</p><h1>Quality &amp; Rework</h1>
    <p>First-pass QA outcomes, defect correction, and the effort associated with rework.</p></div>;
}
export function QualityUnavailable() {
  return <div className="sprint-health quality-rework"><QualityHeading /><section className="page-state" role="alert">
    <h2>Quality data is unavailable</h2><p>We couldn’t load the sprint from the API. Check that the ADI API is running, then try again.</p>
    <a className="retry-link" href="/quality-rework">Try again</a></section></div>;
}
function QualitySummary({ data }: { data: QualityReworkResult }) {
  const summary = data.quality_summary;
  return <section className="sprint-summary" aria-labelledby="quality-summary-heading">
    <div className="section-heading"><h2 id="quality-summary-heading">Quality summary</h2><span className="scenario-label">Fictional demo · Sprint / backlog analysis</span></div>
    <dl className="summary-grid">
      <div><dt>Project</dt><dd>{data.sprint.project}</dd></div><div><dt>Backlog</dt><dd>{data.sprint.backlog}</dd></div><div><dt>Sprint</dt><dd>{data.sprint.name}</dd></div>
      <div><dt>Eligible QA stories</dt><dd><strong>{summary.eligible_qa_stories}</strong></dd></div>
      <div><dt>First-pass successes</dt><dd><strong>{summary.first_pass_successes}</strong></dd></div>
      <div><dt>First-pass failures</dt><dd><strong>{summary.first_pass_failures}</strong></dd></div>
      <div><dt>First-pass QA Rate</dt><dd><strong>{formatRate(summary.first_pass_qa_rate)}</strong></dd></div>
      <div><dt>Stories with rework</dt><dd><strong>{summary.stories_with_rework}</strong></dd></div>
      <div><dt>Active rework cycles</dt><dd><strong>{summary.active_rework_cycles_at_sprint_end}</strong></dd></div>
    </dl><p className="quiet-note">A delivery-flow quality signal, not an individual developer-performance metric.</p>
  </section>;
}
export function QualityReworkView({ data }: { data: QualityReworkResult }) {
  return <div className="sprint-health quality-rework"><QualityHeading />
    {data.stories.length === 0 ? <section className="page-state" role="status"><h2>No quality results available</h2>
      <p>No active-scope story results are available for {data.sprint.name} yet.</p></section> : <>
      <QualitySummary data={data} /><FirstPassQA data={data} /><ReworkOverview data={data} /><ReworkEffortSection effort={data.rework_effort} />
    </>}
    <aside className="quality-guidance"><p><a href="/sprint-health">Sprint Health</a> explains how remaining work changed.</p>
      <p><a href="/delivery-flow">Delivery Flow</a> explains where the work moved.</p>
      <p>Quality &amp; Rework explains how QA returns and defect correction affected delivery.</p></aside>
  </div>;
}
