import type { BurndownResult } from "../../../lib/burndown";
import { BurndownChart } from "./burndown-chart";
import { BurndownInsights } from "./burndown-insights";
import { DailyMovementList } from "./daily-movement-list";
import { SprintSummary } from "./sprint-summary";

export function SprintHealthHeading() {
  return <div className="health-heading"><p className="eyebrow">Sprint Intelligence</p><h1>Sprint Health</h1><p>Remaining delivery work and the events behind each movement.</p></div>;
}

export function SprintHealthUnavailable() {
  return <div className="sprint-health"><SprintHealthHeading /><section className="page-state" role="alert">
    <h2>Sprint data is unavailable</h2>
    <p>We couldn’t load the sprint from the API. Check that the ADI API is running, then try again.</p>
    <a className="retry-link" href="/sprint-health">Try again</a>
  </section></div>;
}

export function SprintHealthView({ data }: { data: BurndownResult }) {
  return <div className="sprint-health">
    <SprintHealthHeading />
    <SprintSummary data={data} />
    {data.daily_snapshots.length === 0 ? <section className="page-state" role="status">
      <h2>No daily snapshots available</h2><p>There are no daily observations to display for this sprint yet.</p>
    </section> : <>
      <BurndownChart snapshots={data.daily_snapshots} />
      <DailyMovementList snapshots={data.daily_snapshots} />
      <BurndownInsights insights={data.insights} threshold={data.configuration.flatline_threshold_days} />
    </>}
  </div>;
}
