import type { Cause } from "../../../lib/burndown";
import { causeLabels, signed } from "./format";

export function CauseList({ causes }: { causes: Cause[] }) {
  if (!causes.length) return <p className="quiet-note">No work-unit changes recorded.</p>;
  return <ul className="cause-list">{causes.map((cause) => (
    <li key={cause.event_id}>
      <span>
        <span>{causeLabels[cause.type]} · <strong>{cause.id}</strong></span>
        {cause.work_item_id !== cause.id && <span className="cause-story"> against {cause.work_item_id}</span>}
        <small className="event-reference">{cause.event_id}</small>
      </span>
      <span className="cause-effect" aria-label={`Effect ${signed(cause.effect)}`}>{signed(cause.effect)}</span>
    </li>
  ))}</ul>;
}
