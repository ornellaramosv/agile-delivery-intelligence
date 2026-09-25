import type { FlowDay, FlowSnapshot } from "../../../lib/delivery-flow";

export function DailyFlowMovements({ days, snapshots }: { days: FlowDay[]; snapshots: FlowSnapshot[] }) {
  return <section className="health-section" aria-labelledby="flow-movements-heading">
    <h2 id="flow-movements-heading">Daily flow movements</h2>
    <p className="section-note">Workflow transitions and scope entries. QA returns indicate rework, not employee performance.</p>
    <ol className="flow-days">{days.map((day) => <li key={day.sprint_day}>
      <article aria-label={`Day ${day.sprint_day}`} className="flow-day">
        <div><h3>Day {day.sprint_day}</h3><time className="day-date" dateTime={day.date}>{day.date}</time>
          <p className="section-note">{snapshots.find((s) => s.sprint_day === day.sprint_day)?.total_active_scope ?? "Unavailable"} active User Stories</p></div>
        <div>
          {day.scope_entries.length > 0 && <div className="flow-entry"><h4>{day.sprint_day === 1 ? "Opening scope" : "Scope entered"}</h4>
            <ul>{day.scope_entries.map((entry) => <li key={entry.event_id}><strong>{entry.work_item_id}</strong> · Entered in {entry.to_state}
              <span className="event-reference">{entry.event_id}</span></li>)}</ul>
            {day.sprint_day !== 1 && <p className="quiet-note">Formally added to active scope. The original baseline is unchanged.</p>}
          </div>}
          {day.movements.length === 0 ? <p className="quiet-note">No workflow transitions.</p> : <ul className="flow-transitions">
            {day.movements.map((movement) => {
              const qaReturn = movement.from_state === "QA" && movement.to_state === "Returned to DEV";
              return <li key={movement.event_id} className={qaReturn ? "flow-qa-return" : undefined}>
                <strong>{movement.work_item_id}</strong>{qaReturn && <span className="flow-return-label">QA return · Rework</span>}
                <p>{movement.from_state} → {movement.to_state}</p>
                <span className="event-reference">{movement.event_id}</span>
              </li>;
            })}
          </ul>}
        </div>
      </article>
    </li>)}</ol>
  </section>;
}
