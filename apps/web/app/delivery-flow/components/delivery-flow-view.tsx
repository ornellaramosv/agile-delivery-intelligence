import type { DeliveryFlowResult, FlowSnapshot } from "../../../lib/delivery-flow";
import { FlowTimelineChart } from "./flow-timeline-chart";
import { DailyFlowMovements } from "./daily-flow-movements";
import { flowColor } from "./flow-colors";

export function DeliveryFlowHeading() {
  return <div className="health-heading"><p className="eyebrow">Sprint Intelligence</p>
    <h1>Delivery Flow</h1><p>Where User Stories are located, and how they moved through the sprint.</p>
  </div>;
}

export function DeliveryFlowUnavailable() {
  return <div className="sprint-health delivery-flow"><DeliveryFlowHeading />
    <section className="page-state" role="alert"><h2>Flow data is unavailable</h2>
      <p>We couldn’t load the sprint from the API. Check that the ADI API is running, then try again.</p>
      <a className="retry-link" href="/delivery-flow">Try again</a>
    </section>
  </div>;
}

function FlowSummary({ data, latest }: { data: DeliveryFlowResult; latest?: FlowSnapshot }) {
  return <section className="sprint-summary" aria-labelledby="flow-summary-heading">
    <div className="section-heading"><h2 id="flow-summary-heading">Flow summary</h2><span className="scenario-label">Fictional demo · End-of-day snapshots</span></div>
    <dl className="summary-grid">
      <div><dt>Project</dt><dd>{data.sprint.project}</dd></div>
      <div><dt>Backlog</dt><dd>{data.sprint.backlog}</dd></div>
      <div><dt>Sprint</dt><dd>{data.sprint.name}</dd></div>
      <div><dt>Active scope{latest ? ` at Day ${latest.sprint_day}` : ""}</dt><dd><strong>{latest?.total_active_scope ?? "Unavailable"}</strong></dd></div>
      <div><dt>Closed User Stories</dt><dd><strong>{latest?.closed_stories ?? "Unavailable"}</strong></dd></div>
      <div><dt>Open User Stories</dt><dd><strong>{latest?.open_stories ?? "Unavailable"}</strong></dd></div>
    </dl>
    <p className="quiet-note">Active scope includes Closed stories. Scope added during the sprint does not change the original baseline.</p>
  </section>;
}

function CurrentFlowComposition({ snapshot, states }: { snapshot: FlowSnapshot; states: string[] }) {
  return <section className="health-section chart-section" aria-labelledby="current-flow-heading">
    <h2 id="current-flow-heading">Current flow composition</h2>
    <p className="section-note">Day {snapshot.sprint_day} · {snapshot.date} · User Stories</p>
    <dl className="flow-composition">
      {states.map((state, index) => <div key={state}>
        <dt><span className="flow-swatch" style={{ background: flowColor(index) }} />{state}</dt>
        <dd>{snapshot.states[state]}</dd>
      </div>)}
    </dl>
  </section>;
}

export function DeliveryFlowView({ data }: { data: DeliveryFlowResult }) {
  const latest = data.daily_snapshots.at(-1);
  return <div className="sprint-health delivery-flow">
    <DeliveryFlowHeading />
    <FlowSummary data={data} latest={latest} />
    {!latest ? <section className="page-state health-section" role="status"><h2>No flow snapshots available</h2>
      <p>There are no daily workflow observations to display for this sprint yet.</p></section> : <>
      <CurrentFlowComposition snapshot={latest} states={data.workflow_states} />
      <FlowTimelineChart snapshots={data.daily_snapshots} states={data.workflow_states} />
      <DailyFlowMovements days={data.daily_movements} snapshots={data.daily_snapshots} />
    </>}
    <aside className="flow-guidance"><p><a href="/sprint-health">Burndown</a> answers: How much delivery work remains?</p>
      <p>Delivery Flow answers: Where are the User Stories currently located?</p>
      <p className="quiet-note">Flow counts User Stories. Burndown may also include open Bugs that block story closure.</p>
    </aside>
  </div>;
}
