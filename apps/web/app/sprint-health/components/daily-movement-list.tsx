import type { DailySnapshot } from "../../../lib/burndown";
import { CauseList } from "./causes";
import { dateLabel, movementLabels, signed } from "./format";

export function DailyMovementList({ snapshots }: { snapshots: DailySnapshot[] }) {
  return (
    <section className="health-section" aria-labelledby="daily-movement-heading">
      <h2 id="daily-movement-heading">Daily movement explanation</h2>
      <p className="section-note">Net movement shows the daily change. Causal activity preserves each addition and closure.</p>
      <div className="daily-column-headings" aria-hidden="true"><span>Snapshot</span><span>Net movement</span><span>Causal activity</span></div>
      <ol className="daily-list">
        {snapshots.map((snapshot, index) => {
          const previous = snapshots[index - 1];
          const explanation = snapshot.explanation;
          return (
            <li key={snapshot.sprint_day}>
              <article className="daily-row" aria-labelledby={`day-${snapshot.sprint_day}`}>
                <div>
                  <h3 id={`day-${snapshot.sprint_day}`}>Day {snapshot.sprint_day}</h3>
                  <time className="day-date" dateTime={snapshot.date}>{dateLabel(snapshot.date)}</time>
                </div>
                <div className="net-movement">
                  <span className={`movement-label movement-${explanation.movement ?? "initial"}`}>
                    {explanation.movement ? movementLabels[explanation.movement] : "Initial snapshot"}
                  </span>
                  <p className="remaining-transition"><span className="sr-only">Remaining work: </span>{previous ? `${previous.current_remaining_work} → ${snapshot.current_remaining_work}` : `— → ${snapshot.current_remaining_work}`}</p>
                  <p className="net-delta">Net delta: <strong>{signed(explanation.delta)}</strong></p>
                </div>
                <div className="daily-causes">
                  <span className="mobile-label">Causal activity</span>
                  {index === 0 && !explanation.causes.length
                    ? <p className="quiet-note">Opening observation. No previous-day comparison.</p>
                    : <CauseList causes={explanation.causes} />}
                </div>
              </article>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
