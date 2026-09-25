import type { Insight } from "../../../lib/burndown";
import { CauseList } from "./causes";
import { signed } from "./format";

export function BurndownInsights({ insights, threshold }: { insights: Insight[]; threshold: number }) {
  return (
    <section className="health-section" aria-labelledby="insights-heading">
      <h2 id="insights-heading">Insights</h2>
      <p className="section-note">Detected from delivery events. Flatlines require {threshold} consecutive Flat days; upward days are separate.</p>
      {!insights.length ? <p className="quiet-note">No insights returned for this sprint.</p> : <ul className="insight-list">{insights.map((insight) => (
        <li key={insight.type === "upward_movement" ? `up-${insight.sprint_day}` : `flat-${insight.start_day}-${insight.end_day}`}>
          {insight.type === "upward_movement" ? <article aria-label={`Upward Movement, Day ${insight.sprint_day}`}>
            <span className="insight-kind insight-up">Upward Movement</span>
            <h3>Day {insight.sprint_day} · {insight.previous_remaining} → {insight.current_remaining}</h3>
            <p className="section-note">Net delta: {signed(insight.delta)} delivery work items</p>
            <CauseList causes={insight.causes} />
          </article> : <article aria-label={`Flatline, Days ${insight.start_day}–${insight.end_day}`}>
            <span className="insight-kind insight-flat">Flatline</span>
            <h3>Days {insight.start_day}–{insight.end_day}</h3>
            <p>{insight.remaining_work} remaining delivery work items</p>
            <p className="section-note">{insight.number_of_days} consecutive Flat days. Zero net movement can still include causal activity.</p>
            {insight.contributing_context.map((context) => context.causes.length > 0 && <div key={context.sprint_day} className="insight-context">
              <h4>Day {context.sprint_day} activity</h4><CauseList causes={context.causes} />
            </div>)}
          </article>}
        </li>
      ))}</ul>}
    </section>
  );
}
