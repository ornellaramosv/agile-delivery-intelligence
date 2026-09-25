import { SprintHealthHeading } from "./components/sprint-health-view";
import "./sprint-health.css";

export default function LoadingSprintHealth() {
  return <div className="sprint-health"><SprintHealthHeading /><section className="page-state" role="status" aria-live="polite" aria-busy="true">
    <h2>Loading Sprint Health…</h2><p>Retrieving delivery snapshots and causal explanations.</p>
  </section></div>;
}
